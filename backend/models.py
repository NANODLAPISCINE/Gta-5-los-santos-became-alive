from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid

# Enums pour les types de PNJ
class NPCType(str, Enum):
    CIVILIAN = "civilian"
    CRIMINAL = "criminal"
    POLICE = "police"
    SHOPKEEPER = "shopkeeper"
    WORKER = "worker"

class NPCMood(str, Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    ANGRY = "angry"
    SCARED = "scared"
    EXCITED = "excited"
    STRESSED = "stressed"

class ActivityType(str, Enum):
    WORKING = "working"
    SHOPPING = "shopping"
    DRIVING = "driving"
    WALKING = "walking"
    SOCIALIZING = "socializing"
    CRIMINAL_ACTIVITY = "criminal_activity"
    PATROLLING = "patrolling"
    SLEEPING = "sleeping"
    EATING = "eating"

# Modèles de base
class Location(BaseModel):
    x: float
    y: float
    z: float
    area_name: str = ""

class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    description: str
    participants: List[str] = []
    location: Optional[Location] = None
    importance: int = Field(default=5, ge=1, le=10)  # 1-10 scale

class NPCPersonality(BaseModel):
    aggression: int = Field(default=5, ge=1, le=10)
    honesty: int = Field(default=5, ge=1, le=10)
    sociability: int = Field(default=5, ge=1, le=10)
    intelligence: int = Field(default=5, ge=1, le=10)
    courage: int = Field(default=5, ge=1, le=10)
    wealth_level: int = Field(default=5, ge=1, le=10)

class NPCSchedule(BaseModel):
    hour: int = Field(ge=0, le=23)
    activity: ActivityType
    location_preference: str = ""
    priority: int = Field(default=5, ge=1, le=10)

class NPC(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    npc_type: NPCType
    personality: NPCPersonality
    current_location: Location
    current_mood: NPCMood = NPCMood.NEUTRAL
    current_activity: ActivityType = ActivityType.WALKING
    
    # Schedule et comportements
    schedule: List[NPCSchedule] = []
    
    # Mémoire
    short_term_memory: List[Memory] = []
    long_term_memory: List[Memory] = []
    
    # Relations avec autres PNJ/joueur
    relationships: Dict[str, int] = {}  # npc_id -> relationship_score (-10 to +10)
    
    # État actuel
    health: int = Field(default=100, ge=0, le=100)
    stress_level: int = Field(default=0, ge=0, le=100)
    last_decision_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Modèles pour les requêtes API
class NPCCreate(BaseModel):
    name: str
    npc_type: NPCType
    personality: Optional[NPCPersonality] = None
    current_location: Location

class NPCUpdate(BaseModel):
    current_location: Optional[Location] = None
    current_mood: Optional[NPCMood] = None
    current_activity: Optional[ActivityType] = None
    health: Optional[int] = None
    stress_level: Optional[int] = None

class DecisionRequest(BaseModel):
    npc_id: str
    context: Dict[str, Any]  # Informations sur l'environnement actuel
    nearby_npcs: List[str] = []
    time_of_day: int = Field(ge=0, le=23)
    weather: str = "sunny"

class DecisionResponse(BaseModel):
    action: str
    target_location: Optional[Location] = None
    interaction_target: Optional[str] = None
    dialogue: Optional[str] = None
    reasoning: str

class GameEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    location: Location
    participants: List[str]
    description: str
    severity: int = Field(default=1, ge=1, le=10)