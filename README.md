# 🎮 Living Los Santos AI - Mod GTA 5 avec PNJ IA Indépendants

Un mod révolutionnaire pour GTA 5 qui transforme Los Santos en une ville vivante où chaque PNJ (Personnage Non-Joueur) possède une intelligence artificielle indépendante propulsée par OpenAI GPT.

## 🌟 Fonctionnalités Principales

### 🧠 IA Avancée pour PNJ
- **Intelligence OpenAI GPT** : Chaque PNJ prend des décisions autonomes basées sur sa personnalité
- **Mémoire persistante** : Les PNJ se souviennent des interactions et événements
- **Personnalités uniques** : Chaque PNJ a ses propres traits (agressivité, honnêteté, sociabilité, etc.)
- **Prise de décision contextuelle** : Actions basées sur l'heure, la météo, et l'environnement

### 🏙️ Los Santos Vivante
- **Rythmes réalistes** : Trafic dense aux heures de pointe, moins de monde la nuit
- **Activités criminelles** : Braquages spontanés planifiés par les PNJ criminels
- **Police réaliste** : Patrouilles intelligentes et réponses aux crimes
- **Interactions sociales** : Conversations entre PNJ et avec le joueur
- **Commerce dynamique** : Magasins ouverts/fermés selon les horaires

### 💾 Système de Mémoire
- **Mémoire à court terme** : Événements récents (20 derniers)
- **Mémoire à long terme** : Expériences marquantes (100 plus importantes)
- **Relations interpersonnelles** : Système de réputation entre PNJ
- **Reconnaissance du joueur** : Les PNJ se souviennent de vos actions

## 🏗️ Architecture Technique

```
GTA 5 Mod (C#) ←→ Backend IA (FastAPI) ←→ OpenAI GPT
      ↓                    ↓
   Contrôle PNJ      MongoDB (Mémoires)
      ↓                    ↓
   Los Santos      Interface Web (Monitoring)
```

### Composants :
1. **Backend IA** (Python/FastAPI) - Cerveau central du système
2. **Mod GTA 5** (C#/ScriptHookVDotNet) - Interface avec le jeu
3. **Base de données** (MongoDB) - Stockage des mémoires et profils
4. **Interface Web** (React) - Monitoring et gestion des PNJ

## 🚀 Installation

### Prérequis
- GTA V installé
- ScriptHookV + ScriptHookVDotNet
- Python 3.8+
- Node.js 16+
- MongoDB

### 1. Backend IA
```bash
cd backend
pip install -r requirements.txt
python server.py
```

### 2. Interface Web
```bash
cd frontend
yarn install
yarn start
```

### 3. Mod GTA 5
1. Compilez le projet C# `LivingLosSantosAI.csproj`
2. Copiez `LivingLosSantosAI.dll` dans votre dossier `scripts/` de GTA V
3. Lancez GTA V

## 🎮 Utilisation

### Contrôles In-Game
- **F7** : Créer de nouveaux PNJ IA
- **F8** : Forcer mise à jour des décisions IA
- **F9** : Afficher statistiques des PNJ

### Interface Web
Accédez à `http://localhost:3000` pour :
- 📊 **Dashboard** : Vue d'ensemble du système
- 👥 **Gestion PNJ** : Détails et contrôle des PNJ
- 📝 **Événements** : Historique des crimes et interactions
- ⚙️ **Simulation** : Contrôles de routine

## 🔧 Configuration

### Variables d'Environnement (backend/.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="gta5_ai_mod"
OPENAI_API_KEY="votre_clé_openai"
```

### Configuration du Mod
- **maxNpcs** : Nombre maximum de PNJ gérés (défaut: 50)
- **backendUrl** : URL du backend IA
- **updateInterval** : Fréquence des mises à jour IA (défaut: 5s)

## 📊 Types de PNJ

### 👨‍💼 Civils
- Activités : Travail, shopping, socialisation
- Horaires : 8h-17h travail, soirées sociales
- Comportement : Évitent les dangers, respectent la loi

### 🚔 Police
- Activités : Patrouilles, interventions
- Disponibilité : 24h/24 par rotation
- Comportement : Répondent aux crimes, poursuivent les suspects

### 🔫 Criminels
- Activités : Braquages, trafic, activités illégales
- Horaires : Surtout la nuit (22h-6h)
- Comportement : Évitent la police, agressifs

### 🏪 Commerçants
- Activités : Gestion de magasin
- Horaires : 9h-21h selon le type de commerce
- Comportement : Amicaux, coopératifs

## 🎯 Fonctionnalités Avancées

### Système de Décision IA
Chaque PNJ prend des décisions basées sur :
- **Personnalité** (10 traits de 1-10)
- **État actuel** (santé, stress, humeur)
- **Contexte environnemental** (heure, météo, trafic)
- **Mémoires** (expériences passées)
- **Relations** (avec autres PNJ et joueur)

### Événements Dynamiques
- **Crimes spontanés** : Braquages, vols de voitures
- **Interventions police** : Réponses réalistes aux crimes
- **Interactions sociales** : Conversations, disputes, amitiés
- **Accidents** : Collisions, incidents de circulation

## 🔍 Monitoring et Debug

### Logs
- **Console GTA V** : Activités du mod
- **Fichier log** : `Documents/LivingLosSantosAI.log`
- **Backend logs** : Console FastAPI
- **Interface web** : Statistiques temps réel

### Statistiques Disponibles
- Nombre total de PNJ par type
- Événements des dernières 24h
- Mémoires stockées par PNJ
- Performance du système IA

## 🛠️ Développement

### Structure du Code
```
/app/
├── backend/           # Système IA (Python/FastAPI)
│   ├── server.py     # Serveur principal
│   ├── ai_engine.py  # Moteur IA OpenAI
│   ├── npc_manager.py # Gestionnaire PNJ
│   └── models.py     # Modèles de données
├── frontend/         # Interface web (React)
│   └── src/App.js   # Application principale
└── gta5_mod/        # Mod GTA 5 (C#)
    └── LivingLosSantosAI.cs # Script principal
```

### API Endpoints
- `POST /api/npcs` : Créer un PNJ
- `GET /api/npcs/{id}` : Détails d'un PNJ
- `POST /api/npcs/{id}/decision` : Décision IA
- `POST /api/events` : Créer un événement
- `GET /api/stats` : Statistiques système

## 🐛 Dépannage

### Problèmes Courants
1. **PNJ ne bougent pas** : Vérifiez la connexion backend
2. **Erreurs IA** : Validez votre clé OpenAI
3. **Performance lente** : Réduisez maxNpcs
4. **Mod ne charge pas** : Vérifiez ScriptHookVDotNet

### Solutions
- Redémarrez le backend si les décisions IA échouent
- Vérifiez les logs pour diagnostiquer les erreurs
- Utilisez F9 in-game pour voir le nombre de PNJ actifs

## 📈 Optimisation

### Performance
- **Limite PNJ** : 50 maximum recommandé
- **Fréquence IA** : 5 secondes entre décisions
- **Nettoyage auto** : PNJ supprimés automatiquement
- **Cache mémoire** : Optimisation des requêtes MongoDB

### Coûts OpenAI
- ~0.002$ par décision PNJ
- Budget quotidien estimé : 5-10$ pour 50 PNJ
- Système de fallback si quota dépassé

## 🤝 Contribution

Contributions bienvenues ! 
1. Fork le projet
2. Créez votre branche feature
3. Committez vos changements
4. Push vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 🎉 Le Futur de Los Santos

Avec Living Los Santos AI, chaque partie devient unique. Les PNJ évoluent, apprennent, et créent des histoires spontanées. Los Santos n'est plus seulement un décor - c'est un monde vivant !

---

**Développé avec ❤️ pour la communauité GTA V**

*"Transformons Los Santos en une vraie métropole intelligente !"*