from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# Import nos modèles et classes
from .models import (
    NPC, NPCCreate, NPCUpdate, DecisionRequest, DecisionResponse,
    GameEvent, Memory, Location, NPCType, ActivityType
)
from .ai_engine import AIEngine
from .npc_manager import NPCManager

# Configuration
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Initialisation des systèmes IA
ai_engine = AIEngine()
npc_manager = NPCManager(db, ai_engine)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="GTA 5 AI NPCs Backend",
    description="Système IA pour contrôler les PNJ dans GTA 5",
    version="1.0.0"
)

# Router avec préfixe /api
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ENDPOINTS PNJ ====================

@api_router.get("/")
async def root():
    """Point d'entrée de base"""
    return {
        "message": "GTA 5 AI NPCs Backend",
        "version": "1.0.0",
        "status": "running"
    }

@api_router.post("/npcs", response_model=NPC)
async def create_npc(npc_data: NPCCreate):
    """Crée un nouveau PNJ avec IA"""
    try:
        npc = await npc_manager.create_npc(npc_data)
        logger.info(f"Nouveau PNJ créé: {npc.name} ({npc.id})")
        return npc
    except Exception as e:
        logger.error(f"Erreur création PNJ: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/npcs", response_model=List[NPC])
async def get_all_npcs():
    """Récupère tous les PNJ"""
    try:
        npcs = await npc_manager.get_all_npcs()
        return npcs
    except Exception as e:
        logger.error(f"Erreur récupération PNJ: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/npcs/{npc_id}", response_model=NPC)
async def get_npc(npc_id: str):
    """Récupère un PNJ spécifique"""
    npc = await npc_manager.get_npc(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="PNJ non trouvé")
    return npc

@api_router.put("/npcs/{npc_id}", response_model=NPC)
async def update_npc(npc_id: str, updates: NPCUpdate):
    """Met à jour un PNJ"""
    npc = await npc_manager.update_npc(npc_id, updates)
    if not npc:
        raise HTTPException(status_code=404, detail="PNJ non trouvé")
    return npc

@api_router.delete("/npcs/{npc_id}")
async def delete_npc(npc_id: str):
    """Supprime un PNJ"""
    result = await db.npcs.delete_one({"id": npc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="PNJ non trouvé")
    return {"message": "PNJ supprimé"}

# ==================== ENDPOINTS IA & DECISIONS ====================

@api_router.post("/npcs/{npc_id}/decision")
async def make_npc_decision(npc_id: str, context: Dict[str, Any]):
    """Fait prendre une décision IA à un PNJ"""
    try:
        decision_result = await npc_manager.process_npc_decision(npc_id, context)
        if "error" in decision_result:
            raise HTTPException(status_code=404, detail=decision_result["error"])
        
        logger.info(f"Décision prise pour PNJ {npc_id}: {decision_result['decision']['action']}")
        return decision_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur décision IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/npcs/{npc_id}/memory")
async def add_npc_memory(npc_id: str, memory_data: Dict[str, Any]):
    """Ajoute une mémoire à un PNJ"""
    try:
        memory = Memory(
            event_type=memory_data.get("event_type", "interaction"),
            description=memory_data["description"],
            participants=memory_data.get("participants", []),
            location=Location(**memory_data["location"]) if memory_data.get("location") else None,
            importance=memory_data.get("importance", 5)
        )
        
        await npc_manager.add_memory(npc_id, memory)
        return {"message": "Mémoire ajoutée", "memory_id": memory.id}
    except Exception as e:
        logger.error(f"Erreur ajout mémoire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/npcs/{npc_id}/nearby")
async def get_nearby_npcs(npc_id: str, radius: float = 100.0):
    """Trouve les PNJ à proximité"""
    npc = await npc_manager.get_npc(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="PNJ non trouvé")
    
    nearby_npcs = await npc_manager.get_nearby_npcs(npc.current_location, radius)
    return [{"id": n.id, "name": n.name, "npc_type": n.npc_type} for n in nearby_npcs]

# ==================== SIMULATION & ROUTINES ====================

@api_router.post("/simulation/daily-routine")
async def run_daily_routine():
    """Lance la routine quotidienne pour tous les PNJ"""
    try:
        current_hour = datetime.now().hour
        npcs = await npc_manager.get_all_npcs()
        
        results = []
        for npc in npcs:
            await npc_manager.simulate_daily_routine(npc.id, current_hour)
            results.append({"npc_id": npc.id, "name": npc.name, "processed": True})
        
        return {
            "message": f"Routine quotidienne exécutée pour {len(results)} PNJ",
            "hour": current_hour,
            "processed_npcs": results
        }
    except Exception as e:
        logger.error(f"Erreur routine quotidienne: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/simulation/bulk-decisions")
async def process_bulk_decisions(npc_contexts: List[Dict[str, Any]]):
    """Traite les décisions pour plusieurs PNJ en même temps"""
    try:
        results = []
        
        for context_data in npc_contexts:
            npc_id = context_data["npc_id"]
            context = context_data["context"]
            
            decision_result = await npc_manager.process_npc_decision(npc_id, context)
            results.append(decision_result)
        
        return {
            "message": f"Décisions traitées pour {len(results)} PNJ",
            "results": results
        }
    except Exception as e:
        logger.error(f"Erreur décisions groupées: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ÉVÉNEMENTS DU JEU ====================

@api_router.post("/events")
async def create_game_event(event_data: Dict[str, Any]):
    """Crée un événement du jeu (crime, accident, etc.)"""
    try:
        event = GameEvent(
            event_type=event_data["event_type"],
            location=Location(**event_data["location"]),
            participants=event_data.get("participants", []),
            description=event_data["description"],
            severity=event_data.get("severity", 5)
        )
        
        # Sauvegarder l'événement
        await db.events.insert_one(event.model_dump())
        
        # Notifier les PNJ à proximité
        nearby_npcs = await npc_manager.get_nearby_npcs(event.location, radius=200.0)
        
        for npc in nearby_npcs:
            memory = Memory(
                event_type="witnessed_event",
                description=f"A été témoin de: {event.description}",
                location=event.location,
                importance=min(event.severity, 8)
            )
            await npc_manager.add_memory(npc.id, memory)
        
        return {
            "event_id": event.id,
            "message": "Événement créé",
            "notified_npcs": len(nearby_npcs)
        }
    except Exception as e:
        logger.error(f"Erreur création événement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/events")
async def get_recent_events(limit: int = 50):
    """Récupère les événements récents"""
    try:
        cursor = db.events.find().sort("timestamp", -1).limit(limit)
        events = []
        async for event_data in cursor:
            # Convert ObjectId to string
            if '_id' in event_data:
                event_data['_id'] = str(event_data['_id'])
            events.append(event_data)
        return events
    except Exception as e:
        logger.error(f"Erreur récupération événements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATISTIQUES ====================

@api_router.get("/stats")
async def get_system_stats():
    """Statistiques du système"""
    try:
        total_npcs = await db.npcs.count_documents({})
        total_events = await db.events.count_documents({})
        
        # Compter par type de PNJ
        npc_types = {}
        for npc_type in NPCType:
            count = await db.npcs.count_documents({"npc_type": npc_type.value})
            npc_types[npc_type.value] = count
        
        # Événements récents (dernières 24h)
        yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_events = await db.events.count_documents({"timestamp": {"$gte": yesterday}})
        
        return {
            "total_npcs": total_npcs,
            "npc_types": npc_types,
            "total_events": total_events,
            "recent_events_24h": recent_events,
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur statistiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UTILITAIRES ====================

@api_router.post("/npcs/create-sample")
async def create_sample_npcs():
    """Crée des PNJ d'example pour tester"""
    try:
        sample_npcs = [
            NPCCreate(
                name="Marcus Johnson",
                npc_type=NPCType.CIVILIAN,
                current_location=Location(x=-1037.0, y=-2738.0, z=20.0, area_name="Los Santos International Airport")
            ),
            NPCCreate(
                name="Officer Rodriguez",
                npc_type=NPCType.POLICE,
                current_location=Location(x=425.0, y=-979.0, z=30.0, area_name="Mission Row Police Station")
            ),
            NPCCreate(
                name="Tommy 'The Snake' Williams",
                npc_type=NPCType.CRIMINAL,
                current_location=Location(x=-1393.0, y=-584.0, z=30.0, area_name="Del Perro")
            ),
            NPCCreate(
                name="Sarah Chen",
                npc_type=NPCType.SHOPKEEPER,
                current_location=Location(x=-707.0, y=-914.0, z=19.0, area_name="Little Seoul")
            )
        ]
        
        created_npcs = []
        for npc_data in sample_npcs:
            npc = await npc_manager.create_npc(npc_data)
            created_npcs.append({"id": npc.id, "name": npc.name, "type": npc.npc_type})
        
        return {
            "message": f"{len(created_npcs)} PNJ d'exemple créés",
            "npcs": created_npcs
        }
    except Exception as e:
        logger.error(f"Erreur création PNJ exemple: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Inclure le router dans l'app
app.include_router(api_router)

# Event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Backend IA GTA 5 démarré")
    logger.info(f"Base de données: {db_name}")
    logger.info("Système IA prêt pour les PNJ")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Arrêt du backend IA GTA 5")
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)