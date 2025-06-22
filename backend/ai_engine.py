import openai
import os
import json
from typing import Dict, List, Any
from models import NPC, DecisionRequest, DecisionResponse, NPCType, NPCMood, ActivityType, Location
from datetime import datetime
import random

class AIEngine:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
    async def make_decision(self, npc: NPC, request: DecisionRequest) -> DecisionResponse:
        """Utilise OpenAI GPT pour faire prendre une décision intelligente au PNJ"""
        
        context_prompt = self._build_context_prompt(npc, request)
        
        try:
            response = await self._call_openai(context_prompt)
            decision = self._parse_decision_response(response)
            return decision
            
        except Exception as e:
            print(f"Erreur IA pour NPC {npc.id}: {e}")
            # Fallback vers décision simple si OpenAI échoue
            return self._fallback_decision(npc, request)
    
    def _build_context_prompt(self, npc: NPC, request: DecisionRequest) -> str:
        """Construit le prompt contextuel pour OpenAI"""
        
        # Informations sur le PNJ
        personality_desc = f"""
        Agressivité: {npc.personality.aggression}/10
        Honnêteté: {npc.personality.honesty}/10
        Sociabilité: {npc.personality.sociability}/10
        Intelligence: {npc.personality.intelligence}/10
        Courage: {npc.personality.courage}/10
        Niveau de richesse: {npc.personality.wealth_level}/10
        """
        
        # Mémoires récentes
        recent_memories = []
        for memory in npc.short_term_memory[-5:]:  # 5 dernières mémoires
            recent_memories.append(f"- {memory.description} ({memory.timestamp.strftime('%H:%M')})")
        
        memories_text = "\n".join(recent_memories) if recent_memories else "Aucune mémoire récente"
        
        # Contexte actuel
        time_context = self._get_time_context(request.time_of_day)
        location_context = self._get_location_context(npc.current_location)
        
        prompt = f"""
Tu es {npc.name}, un {npc.npc_type.value} dans Los Santos (GTA 5). Tu dois prendre une décision réaliste basée sur ton contexte.

PERSONNALITÉ:
{personality_desc}

ÉTAT ACTUEL:
- Humeur: {npc.current_mood.value}
- Activité: {npc.current_activity.value}
- Santé: {npc.health}/100
- Stress: {npc.stress_level}/100
- Position: {location_context}

CONTEXTE TEMPOREL:
- Heure: {request.time_of_day}h
- {time_context}
- Météo: {request.weather}

MÉMOIRES RÉCENTES:
{memories_text}

CONTEXTE ENVIRONNEMENTAL:
{json.dumps(request.context, indent=2)}

PNJ À PROXIMITÉ: {len(request.nearby_npcs)} personnes

INSTRUCTIONS:
En tant que {npc.name}, décide de ton action suivante. Sois réaliste selon ton type ({npc.npc_type.value}) et ta personnalité.

Réponds UNIQUEMENT au format JSON suivant:
{{
    "action": "description_action",
    "target_location": {{"x": 0.0, "y": 0.0, "z": 0.0, "area_name": "nom_zone"}},
    "interaction_target": "id_cible_ou_null",
    "dialogue": "ce_que_tu_dis_ou_null",
    "reasoning": "pourquoi_cette_decision"
}}

Actions possibles: conduire, marcher, parler, acheter, travailler, patrouiller, commettre_crime, fuir, se_cacher, socialiser, dormir, manger
"""
        
        return prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """Appelle l'API OpenAI"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant IA qui contrôle des PNJ dans GTA 5. Réponds toujours en JSON valide."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _parse_decision_response(self, response: str) -> DecisionResponse:
        """Parse la réponse JSON d'OpenAI"""
        try:
            # Nettoyer la réponse (parfois GPT ajoute ```json```)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            target_location = None
            if data.get("target_location"):
                target_location = Location(**data["target_location"])
            
            return DecisionResponse(
                action=data.get("action", "marcher"),
                target_location=target_location,
                interaction_target=data.get("interaction_target"),
                dialogue=data.get("dialogue"),
                reasoning=data.get("reasoning", "Décision par défaut")
            )
            
        except Exception as e:
            print(f"Erreur parsing réponse IA: {e}")
            print(f"Réponse brute: {response}")
            raise
    
    def _fallback_decision(self, npc: NPC, request: DecisionRequest) -> DecisionResponse:
        """Décision de secours si OpenAI échoue"""
        actions = ["marcher", "conduire", "socialiser"]
        
        if npc.npc_type == NPCType.CRIMINAL:
            actions.extend(["commettre_crime", "se_cacher"])
        elif npc.npc_type == NPCType.POLICE:
            actions.extend(["patrouiller"])
        
        action = random.choice(actions)
        
        return DecisionResponse(
            action=action,
            target_location=None,
            interaction_target=None,
            dialogue=None,
            reasoning="Décision de secours - IA indisponible"
        )
    
    def _get_time_context(self, hour: int) -> str:
        """Retourne le contexte selon l'heure"""
        if 6 <= hour <= 9:
            return "Heure de pointe matinale - beaucoup de trafic, les gens vont au travail"
        elif 9 <= hour <= 17:
            return "Heures de bureau - activité normale, commerces ouverts"
        elif 17 <= hour <= 19:
            return "Heure de pointe du soir - trafic dense, les gens rentrent"
        elif 19 <= hour <= 23:
            return "Soirée - bars et restaurants actifs, moins de monde dans les rues"
        else:
            return "Nuit - peu de monde, activité criminelle possible, commerces fermés"
    
    def _get_location_context(self, location: Location) -> str:
        """Retourne le contexte selon la zone"""
        area = location.area_name.lower()
        
        if "downtown" in area or "center" in area:
            return "Centre-ville - zone d'affaires, beaucoup de monde"
        elif "grove" in area:
            return "Grove Street - quartier résidentiel"
        elif "vinewood" in area:
            return "Vinewood - quartier huppé"
        elif "beach" in area:
            return "Plage - zone touristique"
        elif "industrial" in area:
            return "Zone industrielle - entrepôts et usines"
        else:
            return f"Zone: {location.area_name}"