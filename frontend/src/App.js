import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Composant principal de gestion des PNJ
const NPCManager = () => {
  const [npcs, setNpcs] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedNpc, setSelectedNpc] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  // Chargement initial des données
  useEffect(() => {
    loadInitialData();
    // Rafraîchir les données toutes les 10 secondes
    const interval = setInterval(loadInitialData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    try {
      const [npcsRes, statsRes, eventsRes] = await Promise.all([
        axios.get(`${API}/npcs`),
        axios.get(`${API}/stats`),
        axios.get(`${API}/events?limit=20`)
      ]);
      
      setNpcs(npcsRes.data);
      setStats(statsRes.data);
      setEvents(eventsRes.data);
      setLoading(false);
    } catch (error) {
      console.error("Erreur chargement données:", error);
      setLoading(false);
    }
  };

  const createSampleNpcs = async () => {
    try {
      await axios.post(`${API}/npcs/create-sample`);
      await loadInitialData();
    } catch (error) {
      console.error("Erreur création PNJ:", error);
    }
  };

  const runDailyRoutine = async () => {
    try {
      await axios.post(`${API}/simulation/daily-routine`);
      await loadInitialData();
    } catch (error) {
      console.error("Erreur routine quotidienne:", error);
    }
  };

  const makeNpcDecision = async (npcId) => {
    try {
      const context = {
        weather: "sunny",
        traffic_density: 7,
        police_presence: 3,
        time_context: "normal_day"
      };
      
      const response = await axios.post(`${API}/npcs/${npcId}/decision`, context);
      console.log("Décision PNJ:", response.data);
      await loadInitialData();
    } catch (error) {
      console.error("Erreur décision PNJ:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Chargement du système IA...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-400">
            🎮 GTA 5 AI NPCs Manager
          </h1>
          <div className="flex space-x-4">
            <span className="px-3 py-1 bg-green-600 rounded-full text-sm">
              {stats.total_npcs || 0} PNJ Actifs
            </span>
            <span className="px-3 py-1 bg-blue-600 rounded-full text-sm">
              Système Opérationnel
            </span>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {['dashboard', 'npcs', 'events', 'simulation'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Dashboard */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold text-blue-400 mb-2">Total PNJ</h3>
                <p className="text-3xl font-bold">{stats.total_npcs || 0}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold text-green-400 mb-2">Civils</h3>
                <p className="text-3xl font-bold">{stats.npc_types?.civilian || 0}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold text-red-400 mb-2">Criminels</h3>
                <p className="text-3xl font-bold">{stats.npc_types?.criminal || 0}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">Police</h3>
                <p className="text-3xl font-bold">{stats.npc_types?.police || 0}</p>
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold mb-4">Actions Rapides</h3>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={createSampleNpcs}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Créer PNJ d'Exemple
                </button>
                <button
                  onClick={runDailyRoutine}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                >
                  Lancer Routine Quotidienne
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Liste des PNJ */}
        {activeTab === "npcs" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Gestion des PNJ</h2>
              <button
                onClick={createSampleNpcs}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                + Ajouter PNJ
              </button>
            </div>

            <div className="grid gap-4">
              {npcs.map((npc) => (
                <div key={npc.id} className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold">{npc.name}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          npc.npc_type === 'civilian' ? 'bg-green-600' :
                          npc.npc_type === 'criminal' ? 'bg-red-600' :
                          npc.npc_type === 'police' ? 'bg-blue-600' : 'bg-gray-600'
                        }`}>
                          {npc.npc_type}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          npc.current_mood === 'happy' ? 'bg-yellow-600' :
                          npc.current_mood === 'angry' ? 'bg-red-600' :
                          npc.current_mood === 'scared' ? 'bg-purple-600' : 'bg-gray-600'
                        }`}>
                          {npc.current_mood}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
                        <div>
                          <p><strong>Activité:</strong> {npc.current_activity}</p>
                          <p><strong>Santé:</strong> {npc.health}/100</p>
                          <p><strong>Stress:</strong> {npc.stress_level}/100</p>
                        </div>
                        <div>
                          <p><strong>Position:</strong> {npc.current_location.area_name || "Zone inconnue"}</p>
                          <p><strong>Mémoires:</strong> {npc.short_term_memory.length}</p>
                          <p><strong>Relations:</strong> {Object.keys(npc.relationships).length}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={() => makeNpcDecision(npc.id)}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-sm transition-colors"
                      >
                        Décision IA
                      </button>
                      <button
                        onClick={() => setSelectedNpc(npc)}
                        className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm transition-colors"
                      >
                        Détails
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Événements */}
        {activeTab === "events" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Événements Récents</h2>
            
            <div className="space-y-4">
              {events.map((event) => (
                <div key={event.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-white">{event.event_type}</h3>
                      <p className="text-gray-300 text-sm mt-1">{event.description}</p>
                      <p className="text-gray-500 text-xs mt-2">
                        {new Date(event.timestamp).toLocaleString()} - 
                        Participants: {event.participants.length} - 
                        Sévérité: {event.severity}/10
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      event.severity >= 7 ? 'bg-red-600' :
                      event.severity >= 4 ? 'bg-yellow-600' : 'bg-green-600'
                    }`}>
                      Niveau {event.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Simulation */}
        {activeTab === "simulation" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Contrôles de Simulation</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold mb-4">Routines Automatiques</h3>
                <div className="space-y-3">
                  <button
                    onClick={runDailyRoutine}
                    className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                  >
                    Exécuter Routine Quotidienne
                  </button>
                  <button
                    onClick={() => {
                      npcs.forEach(npc => makeNpcDecision(npc.id));
                    }}
                    className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                  >
                    Décisions IA en Masse
                  </button>
                </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold mb-4">Statistiques Temps Réel</h3>
                <div className="space-y-2 text-sm">
                  <p><strong>Événements 24h:</strong> {stats.recent_events_24h || 0}</p>
                  <p><strong>Dernière MAJ:</strong> {new Date().toLocaleTimeString()}</p>
                  <p><strong>Status:</strong> 
                    <span className="text-green-400 ml-2">Opérationnel</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal détails PNJ */}
      {selectedNpc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">{selectedNpc.name}</h2>
              <button
                onClick={() => setSelectedNpc(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4 text-sm">
              <div>
                <h3 className="font-semibold text-blue-400 mb-2">Personnalité</h3>
                <div className="grid grid-cols-2 gap-2">
                  <p>Agressivité: {selectedNpc.personality.aggression}/10</p>
                  <p>Honnêteté: {selectedNpc.personality.honesty}/10</p>
                  <p>Sociabilité: {selectedNpc.personality.sociability}/10</p>
                  <p>Intelligence: {selectedNpc.personality.intelligence}/10</p>
                  <p>Courage: {selectedNpc.personality.courage}/10</p>
                  <p>Richesse: {selectedNpc.personality.wealth_level}/10</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-green-400 mb-2">Mémoires Récentes</h3>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {selectedNpc.short_term_memory.slice(-5).map((memory, index) => (
                    <p key={index} className="text-gray-300">
                      • {memory.description}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <NPCManager />
    </div>
  );
}

export default App;