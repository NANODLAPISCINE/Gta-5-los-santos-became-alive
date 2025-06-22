from motor.motor_asyncio import AsyncIOMotorCollection
from .models import NPC, NPCCreate, NPCUpdate, Memory, GameEvent, NPCType, NPCPersonality, Location, ActivityType
from ai_engine import AIEngine
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import uuid

class NPCManager:
    def __init__(self, db, ai_engine: AIEngine):
        self.db = db
        self.npcs_collection: AsyncIOMotorCollection = db.npcs
        self.events_collection: AsyncIOMotorCollection = db.events
        self.ai_engine = ai_engine
        
    async def create_npc(self, npc_data: NPCCreate) -> NPC:
        """Crée un nouveau PNJ avec personnalité générée"""
        
        # Générer personnalité si pas fournie
        personality = npc_data.personality or self._generate_personality(npc_data.npc_type)
        
        npc = NPC(
            name=npc_data.name,
            npc_type=npc_data.npc_type,
            personality=personality,
            current_location=npc_data.current_location,
            schedule=self._generate_schedule(npc_data.npc_type)
        )
        
        # Sauvegarder en base
        await self.npcs_collection.insert_one(npc.model_dump())
        return npc
    
    async def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Récupère un PNJ par son ID"""
        npc_data = await self.npcs_collection.find_one({"id": npc_id})
        if npc_data:
            return NPC(**npc_data)
        return None
    
    async def get_all_npcs(self) -> List[NPC]:
        """Récupère tous les PNJ"""
        cursor = self.npcs_collection.find()
        npcs = []
        async for npc_data in cursor:
            npcs.append(NPC(**npc_data))
        return npcs
    
    async def update_npc(self, npc_id: str, updates: NPCUpdate) -> Optional[NPC]:
        """Met à jour un PNJ"""
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["last_updated"] = datetime.utcnow()
        
        await self.npcs_collection.update_one(
            {"id": npc_id},
            {"$set": update_data}
        )
        
        return await self.get_npc(npc_id)
    
    async def add_memory(self, npc_id: str, memory: Memory):
        """Ajoute une mémoire à un PNJ"""
        npc = await self.get_npc(npc_id)
        if not npc:
            return
        
        # Ajouter à la mémoire court terme
        npc.short_term_memory.append(memory)
        
        # Limiter la mémoire court terme à 20 éléments
        if len(npc.short_term_memory) > 20:
            # Déplacer les plus anciennes vers long terme si importantes
            old_memory = npc.short_term_memory.pop(0)
            if old_memory.importance >= 7:
                npc.long_term_memory.append(old_memory)
        
        # Limiter la mémoire long terme à 100 éléments
        if len(npc.long_term_memory) > 100:
            npc.long_term_memory.pop(0)
        
        # Mettre à jour en base
        await self.npcs_collection.update_one(
            {"id": npc_id},
            {"$set": {
                "short_term_memory": [m.model_dump() for m in npc.short_term_memory],
                "long_term_memory": [m.model_dump() for m in npc.long_term_memory],
                "last_updated": datetime.utcnow()
            }}
        )
    
    async def get_nearby_npcs(self, location: Location, radius: float = 100.0) -> List[NPC]:
        """Trouve les PNJ à proximité d'une position"""
        npcs = await self.get_all_npcs()
        nearby = []
        
        for npc in npcs:
            distance = self._calculate_distance(location, npc.current_location)
            if distance <= radius:
                nearby.append(npc)
        
        return nearby
    
    async def process_npc_decision(self, npc_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une décision IA pour un PNJ"""
        npc = await self.get_npc(npc_id)
        if not npc:
            return {"error": "PNJ non trouvé"}
        
        # Construire la requête de décision
        from .models import DecisionRequest
        
        nearby_npcs = await self.get_nearby_npcs(npc.current_location)
        nearby_ids = [n.id for n in nearby_npcs if n.id != npc_id]
        
        decision_request = DecisionRequest(
            npc_id=npc_id,
            context=context,
            nearby_npcs=nearby_ids,
            time_of_day=datetime.now().hour,
            weather=context.get("weather", "sunny")
        )
        
        # Obtenir la décision IA
        decision = await self.ai_engine.make_decision(npc, decision_request)
        
        # Créer une mémoire de cette décision
        memory = Memory(
            event_type="decision",
            description=f"Décision: {decision.action} - {decision.reasoning}",
            location=npc.current_location,
            importance=5
        )
        await self.add_memory(npc_id, memory)
        
        # Mettre à jour l'état du PNJ si nécessaire
        updates = NPCUpdate()
        if decision.target_location:
            updates.current_location = decision.target_location
        
        if updates.model_dump(exclude_none=True):
            await self.update_npc(npc_id, updates)
        
        return {
            "npc_id": npc_id,
            "decision": decision.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def simulate_daily_routine(self, npc_id: str, current_hour: int):
        """Simule la routine quotidienne d'un PNJ"""
        npc = await self.get_npc(npc_id)
        if not npc:
            return
        
        # Trouver l'activité prévue pour cette heure
        scheduled_activity = None
        for schedule_item in npc.schedule:
            if schedule_item.hour == current_hour:
                scheduled_activity = schedule_item
                break
        
        if scheduled_activity:
            # Adapter l'humeur selon l'activité
            new_mood = self._determine_mood_for_activity(
                scheduled_activity.activity, 
                npc.personality,
                npc.stress_level
            )
            
            updates = NPCUpdate(
                current_activity=scheduled_activity.activity,
                current_mood=new_mood
            )
            
            await self.update_npc(npc_id, updates)
            
            # Créer une mémoire de changement d'activité
            memory = Memory(
                event_type="routine",
                description=f"Changement d'activité: {scheduled_activity.activity.value}",
                location=npc.current_location,
                importance=3
            )
            await self.add_memory(npc_id, memory)
    
    def _generate_personality(self, npc_type: NPCType) -> NPCPersonality:
        """Génère une personnalité basée sur le type de PNJ"""
        base_personality = NPCPersonality()
        
        if npc_type == NPCType.CRIMINAL:
            base_personality.aggression = random.randint(7, 10)
            base_personality.honesty = random.randint(1, 4)
            base_personality.courage = random.randint(6, 9)
        elif npc_type == NPCType.POLICE:
            base_personality.honesty = random.randint(7, 10)
            base_personality.courage = random.randint(8, 10)
            base_personality.aggression = random.randint(6, 8)
        elif npc_type == NPCType.CIVILIAN:
            # Valeurs normales avec variation
            base_personality.aggression = random.randint(3, 7)
            base_personality.honesty = random.randint(5, 8)
            base_personality.sociability = random.randint(4, 8)
        
        return base_personality
    
    def _generate_schedule(self, npc_type: NPCType) -> List:
        """Génère un planning quotidien selon le type de PNJ"""
        from models import NPCSchedule
        
        schedule = []
        
        if npc_type == NPCType.CIVILIAN:
            schedule = [
                NPCSchedule(hour=8, activity=ActivityType.WORKING, priority=8),
                NPCSchedule(hour=12, activity=ActivityType.EATING, priority=6),
                NPCSchedule(hour=14, activity=ActivityType.WORKING, priority=8),
                NPCSchedule(hour=18, activity=ActivityType.SHOPPING, priority=5),
                NPCSchedule(hour=20, activity=ActivityType.SOCIALIZING, priority=4),
                NPCSchedule(hour=23, activity=ActivityType.SLEEPING, priority=9)
            ]
        elif npc_type == NPCType.CRIMINAL:
            schedule = [
                NPCSchedule(hour=10, activity=ActivityType.WALKING, priority=3),
                NPCSchedule(hour=14, activity=ActivityType.CRIMINAL_ACTIVITY, priority=7),
                NPCSchedule(hour=22, activity=ActivityType.CRIMINAL_ACTIVITY, priority=8),
                NPCSchedule(hour=2, activity=ActivityType.SLEEPING, priority=6)
            ]
        elif npc_type == NPCType.POLICE:
            schedule = [
                NPCSchedule(hour=8, activity=ActivityType.PATROLLING, priority=9),
                NPCSchedule(hour=12, activity=ActivityType.EATING, priority=5),
                NPCSchedule(hour=13, activity=ActivityType.PATROLLING, priority=9),
                NPCSchedule(hour=20, activity=ActivityType.PATROLLING, priority=8)
            ]
        
        return schedule
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calcule la distance euclidienne entre deux points"""
        return ((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2 + (loc1.z - loc2.z)**2)**0.5
    
    def _determine_mood_for_activity(self, activity: ActivityType, personality: NPCPersonality, stress: int):
        """Détermine l'humeur selon l'activité et la personnalité"""
        from models import NPCMood
        
        if stress > 70:
            return NPCMood.STRESSED
        
        if activity == ActivityType.SOCIALIZING and personality.sociability > 7:
            return NPCMood.HAPPY
        elif activity == ActivityType.CRIMINAL_ACTIVITY and personality.aggression > 7:
            return NPCMood.EXCITED
        elif activity == ActivityType.WORKING:
            return NPCMood.NEUTRAL
        else:
            return NPCMood.NEUTRAL