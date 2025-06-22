using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using GTA;
using GTA.Math;
using GTA.Native;
using Newtonsoft.Json;
using System.IO;

namespace LivingLosSantosAI
{
    public class LivingLosSantosAI : Script
    {
        private readonly HttpClient httpClient;
        private readonly string backendUrl = "https://7c9a49cc-fad5-4687-bd9e-904acccadd50.preview.emergentagent.com/api";
        private readonly Dictionary<int, string> npcToBackendId = new Dictionary<int, string>();
        private readonly List<Ped> managedNpcs = new List<Ped>();
        private readonly Random random = new Random();
        
        private DateTime lastRoutineCheck = DateTime.Now;
        private DateTime lastDecisionUpdate = DateTime.Now;
        private int maxNpcs = 50; // Limite pour les performances
        
        public LivingLosSantosAI()
        {
            httpClient = new HttpClient();
            httpClient.Timeout = TimeSpan.FromSeconds(10);
            
            // Events du script
            Tick += OnTick;
            KeyDown += OnKeyDown;
            
            // Initialisation
            InitializeSystem();
            
            // Log de démarrage
            LogMessage("🎮 Living Los Santos AI - Système démarré");
            UI.Notify($"~g~Living Los Santos AI~w~ activé!");
        }
        
        private async void InitializeSystem()
        {
            try
            {
                // Créer des PNJ d'exemple au démarrage
                await CreateSampleNpcs();
                
                // Démarrer la routine de gestion
                StartManagementRoutine();
                
                LogMessage("Système IA initialisé avec succès");
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur initialisation: {ex.Message}");
            }
        }
        
        private async Task CreateSampleNpcs()
        {
            try
            {
                var response = await httpClient.PostAsync($"{backendUrl}/npcs/create-sample", null);
                if (response.IsSuccessStatusCode)
                {
                    LogMessage("PNJ d'exemple créés dans le backend");
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur création PNJ: {ex.Message}");
            }
        }
        
        private void StartManagementRoutine()
        {
            // Cette méthode sera appelée dans OnTick pour gérer les PNJ
            LogMessage("Routine de gestion des PNJ démarrée");
        }
        
        private async void OnTick(object sender, EventArgs e)
        {
            try
            {
                // Vérifier et nettoyer les PNJ supprimés
                CleanupDeletedNpcs();
                
                // Créer de nouveaux PNJ si nécessaire
                if (managedNpcs.Count < maxNpcs)
                {
                    await SpawnNewNpc();
                }
                
                // Mettre à jour les décisions IA (toutes les 5 secondes)
                if (DateTime.Now - lastDecisionUpdate > TimeSpan.FromSeconds(5))
                {
                    await UpdateNpcDecisions();
                    lastDecisionUpdate = DateTime.Now;
                }
                
                // Routine quotidienne (toutes les heures)
                if (DateTime.Now - lastRoutineCheck > TimeSpan.FromHours(1))
                {
                    await RunDailyRoutine();
                    lastRoutineCheck = DateTime.Now;
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur OnTick: {ex.Message}");
            }
        }
        
        private void CleanupDeletedNpcs()
        {
            var toRemove = new List<Ped>();
            
            for (int i = managedNpcs.Count - 1; i >= 0; i--)
            {
                var npc = managedNpcs[i];
                if (npc == null || !npc.Exists() || npc.IsDead)
                {
                    if (npc != null && npcToBackendId.ContainsKey(npc.Handle))
                    {
                        npcToBackendId.Remove(npc.Handle);
                    }
                    managedNpcs.RemoveAt(i);
                }
            }
        }
        
        private async Task SpawnNewNpc()
        {
            try
            {
                // Positions aléatoires dans Los Santos
                var spawnPositions = new Vector3[]
                {
                    new Vector3(-1037.0f, -2738.0f, 20.0f), // Aéroport
                    new Vector3(425.0f, -979.0f, 30.0f),    // Commissariat
                    new Vector3(-1393.0f, -584.0f, 30.0f),  // Del Perro
                    new Vector3(-707.0f, -914.0f, 19.0f),   // Little Seoul
                    new Vector3(1135.0f, -982.0f, 46.0f),   // Mirror Park
                    new Vector3(-1823.0f, 794.0f, 138.0f),  // Richman
                    new Vector3(-47.0f, -1757.0f, 29.0f),   // Davis
                    new Vector3(1981.0f, 3053.0f, 47.0f)    // Sandy Shores
                };
                
                var position = spawnPositions[random.Next(spawnPositions.Length)];
                
                // Hash des modèles de PNJ
                var npcModels = new PedHash[]
                {
                    PedHash.Business01AFY, PedHash.Business01AMY, PedHash.Business02AFY,
                    PedHash.Business02AMY, PedHash.Business03AFY, PedHash.Business03AMY,
                    PedHash.BusinessCasual01AFY, PedHash.BusinessCasual01AMY,
                    PedHash.Hipster01AFY, PedHash.Hipster01AMY, PedHash.Hipster02AFY,
                    PedHash.Tourist01AFY, PedHash.Tourist01AMY
                };
                
                var model = npcModels[random.Next(npcModels.Length)];
                
                // Créer le PNJ dans le jeu
                var ped = World.CreatePed(model, position);
                if (ped != null && ped.Exists())
                {
                    // Configuration du PNJ
                    ped.CanRagdoll = true;
                    ped.BlockPermanentEvents = false;
                    ped.IsInvincible = false;
                    
                    // Donner des tâches de base
                    ped.Task.WanderAround();
                    
                    // Ajouter à la liste gérée
                    managedNpcs.Add(ped);
                    
                    // Créer dans le backend
                    await CreateNpcInBackend(ped, position);
                    
                    LogMessage($"Nouveau PNJ créé: {ped.Handle} à {position}");
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur spawn PNJ: {ex.Message}");
            }
        }
        
        private async Task CreateNpcInBackend(Ped ped, Vector3 position)
        {
            try
            {
                var npcTypes = new string[] { "civilian", "criminal", "police", "shopkeeper" };
                var randomType = npcTypes[random.Next(npcTypes.Length)];
                
                var npcData = new
                {
                    name = $"PNJ_{ped.Handle}",
                    npc_type = randomType,
                    current_location = new
                    {
                        x = position.X,
                        y = position.Y,
                        z = position.Z,
                        area_name = GetAreaName(position)
                    }
                };
                
                var json = JsonConvert.SerializeObject(npcData);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await httpClient.PostAsync($"{backendUrl}/npcs", content);
                if (response.IsSuccessStatusCode)
                {
                    var responseData = await response.Content.ReadAsStringAsync();
                    var npcInfo = JsonConvert.DeserializeObject<dynamic>(responseData);
                    
                    // Sauvegarder l'ID backend
                    npcToBackendId[ped.Handle] = npcInfo.id;
                    
                    LogMessage($"PNJ créé dans backend: {npcInfo.id}");
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur création backend PNJ: {ex.Message}");
            }
        }
        
        private async Task UpdateNpcDecisions()
        {
            try
            {
                var activePeds = managedNpcs.Where(p => p != null && p.Exists() && !p.IsDead).Take(10).ToList();
                
                foreach (var ped in activePeds)
                {
                    if (npcToBackendId.ContainsKey(ped.Handle))
                    {
                        var backendId = npcToBackendId[ped.Handle];
                        await ProcessNpcDecision(ped, backendId);
                    }
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur mise à jour décisions: {ex.Message}");
            }
        }
        
        private async Task ProcessNpcDecision(Ped ped, string backendId)
        {
            try
            {
                var context = new
                {
                    weather = GetWeatherString(),
                    traffic_density = GetTrafficDensity(),
                    police_presence = GetPolicePresence(),
                    time_context = GetTimeContext(),
                    nearby_player = Game.Player.Character.Position.DistanceTo(ped.Position) < 50
                };
                
                var json = JsonConvert.SerializeObject(context);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await httpClient.PostAsync($"{backendUrl}/npcs/{backendId}/decision", content);
                if (response.IsSuccessStatusCode)
                {
                    var decisionData = await response.Content.ReadAsStringAsync();
                    var decision = JsonConvert.DeserializeObject<dynamic>(decisionData);
                    
                    // Appliquer la décision au PNJ
                    await ApplyDecisionToNpc(ped, decision);
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur traitement décision: {ex.Message}");
            }
        }
        
        private async Task ApplyDecisionToNpc(Ped ped, dynamic decision)
        {
            try
            {
                var action = decision.decision.action.ToString();
                var reasoning = decision.decision.reasoning.ToString();
                
                // Appliquer l'action selon le type
                switch (action.ToLower())
                {
                    case "conduire":
                        await MakeNpcDrive(ped);
                        break;
                        
                    case "marcher":
                        await MakeNpcWalk(ped);
                        break;
                        
                    case "socialiser":
                        await MakeNpcSocialize(ped);
                        break;
                        
                    case "commettre_crime":
                        await MakeNpcCommitCrime(ped);
                        break;
                        
                    case "patrouiller":
                        await MakeNpcPatrol(ped);
                        break;
                        
                    case "fuir":
                        await MakeNpcFlee(ped);
                        break;
                        
                    default:
                        ped.Task.WanderAround();
                        break;
                }
                
                // Dialogue si fourni
                if (decision.decision.dialogue != null)
                {
                    var dialogue = decision.decision.dialogue.ToString();
                    ShowNpcDialogue(ped, dialogue);
                }
                
                LogMessage($"Action appliquée: {action} - {reasoning}");
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur application décision: {ex.Message}");
            }
        }
        
        private async Task MakeNpcDrive(Ped ped)
        {
            try
            {
                var vehicle = World.GetClosestVehicle(ped.Position, 50.0f);
                if (vehicle != null && vehicle.Exists())
                {
                    ped.Task.EnterVehicle(vehicle, VehicleSeat.Driver);
                    await Task.Delay(2000);
                    
                    if (ped.IsInVehicle())
                    {
                        var destination = GenerateRandomDestination(ped.Position);
                        ped.Task.DriveTo(vehicle, destination, 10.0f, 35.0f);
                    }
                }
                else
                {
                    // Créer un véhicule si aucun n'est disponible
                    var vehicleModels = new VehicleHash[] { VehicleHash.Blista, VehicleHash.Dilettante, VehicleHash.Panto };
                    var randomModel = vehicleModels[random.Next(vehicleModels.Length)];
                    
                    var spawnedVehicle = World.CreateVehicle(randomModel, ped.Position);
                    if (spawnedVehicle != null)
                    {
                        ped.Task.EnterVehicle(spawnedVehicle, VehicleSeat.Driver);
                    }
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur conduite PNJ: {ex.Message}");
            }
        }
        
        private async Task MakeNpcWalk(Ped ped)
        {
            var destination = GenerateRandomDestination(ped.Position, 100.0f);
            ped.Task.GoTo(destination);
        }
        
        private async Task MakeNpcSocialize(Ped ped)
        {
            var nearbyPeds = World.GetNearbyPeds(ped.Position, 30.0f);
            var otherPed = nearbyPeds.FirstOrDefault(p => p != ped && p.Exists());
            
            if (otherPed != null)
            {
                ped.Task.TurnTo(otherPed);
                await Task.Delay(1000);
                ped.Task.ChatTo(otherPed);
            }
            else
            {
                ped.Task.WanderAround();
            }
        }
        
        private async Task MakeNpcCommitCrime(Ped ped)
        {
            // Simuler un crime simple (vol de voiture)
            var nearbyVehicles = World.GetNearbyVehicles(ped.Position, 50.0f);
            var targetVehicle = nearbyVehicles.FirstOrDefault(v => v.Exists() && !v.IsPersistent);
            
            if (targetVehicle != null)
            {
                ped.Task.EnterVehicle(targetVehicle, VehicleSeat.Driver);
                
                // Créer un événement de crime dans le backend
                await CreateCrimeEvent(ped, "Vol de véhicule");
            }
        }
        
        private async Task MakeNpcPatrol(Ped ped)
        {
            // Patrouille en marchant en cercle
            var patrolPoints = new Vector3[]
            {
                ped.Position + new Vector3(50, 0, 0),
                ped.Position + new Vector3(0, 50, 0),
                ped.Position + new Vector3(-50, 0, 0),
                ped.Position + new Vector3(0, -50, 0)
            };
            
            var randomPoint = patrolPoints[random.Next(patrolPoints.Length)];
            ped.Task.GoTo(randomPoint);
        }
        
        private async Task MakeNpcFlee(Ped ped)
        {
            var fleeDirection = GenerateRandomDestination(ped.Position, 200.0f);
            ped.Task.FleeFrom(Game.Player.Character, 10000);
        }
        
        private async Task CreateCrimeEvent(Ped ped, string crimeType)
        {
            try
            {
                var eventData = new
                {
                    event_type = "crime",
                    location = new
                    {
                        x = ped.Position.X,
                        y = ped.Position.Y,
                        z = ped.Position.Z,
                        area_name = GetAreaName(ped.Position)
                    },
                    participants = new[] { npcToBackendId.ContainsKey(ped.Handle) ? npcToBackendId[ped.Handle] : "unknown" },
                    description = $"{crimeType} commis par PNJ",
                    severity = random.Next(3, 8)
                };
                
                var json = JsonConvert.SerializeObject(eventData);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                await httpClient.PostAsync($"{backendUrl}/events", content);
                LogMessage($"Événement de crime créé: {crimeType}");
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur création événement crime: {ex.Message}");
            }
        }
        
        private async Task RunDailyRoutine()
        {
            try
            {
                var response = await httpClient.PostAsync($"{backendUrl}/simulation/daily-routine", null);
                if (response.IsSuccessStatusCode)
                {
                    LogMessage("Routine quotidienne exécutée");
                    UI.Notify("~b~Routine quotidienne~w~ mise à jour");
                }
            }
            catch (Exception ex)
            {
                LogMessage($"Erreur routine quotidienne: {ex.Message}");
            }
        }
        
        private void ShowNpcDialogue(Ped ped, string dialogue)
        {
            // Afficher le dialogue au-dessus du PNJ
            if (Game.Player.Character.Position.DistanceTo(ped.Position) < 30)
            {
                UI.ShowSubtitle($"PNJ: {dialogue}", 3000);
            }
        }
        
        private Vector3 GenerateRandomDestination(Vector3 currentPos, float radius = 150.0f)
        {
            var angle = random.NextDouble() * 2 * Math.PI;
            var distance = random.NextDouble() * radius;
            
            var x = currentPos.X + (float)(Math.Cos(angle) * distance);
            var y = currentPos.Y + (float)(Math.Sin(angle) * distance);
            var z = World.GetGroundHeight(new Vector2(x, y));
            
            return new Vector3(x, y, z);
        }
        
        private string GetAreaName(Vector3 position)
        {
            var streetHash = Function.Call<uint>(Hash.GET_STREET_NAME_AT_COORD, position.X, position.Y, position.Z);
            var streetName = Function.Call<string>(Hash.GET_STREET_NAME_FROM_HASH_KEY, streetHash);
            return string.IsNullOrEmpty(streetName) ? "Zone inconnue" : streetName;
        }
        
        private string GetWeatherString()
        {
            var weather = World.Weather;
            return weather.ToString().ToLower();
        }
        
        private int GetTrafficDensity()
        {
            var hour = DateTime.Now.Hour;
            if (hour >= 7 && hour <= 9) return 9; // Rush matinal
            if (hour >= 17 && hour <= 19) return 9; // Rush soir
            if (hour >= 10 && hour <= 16) return 6; // Journée
            if (hour >= 20 && hour <= 23) return 4; // Soirée
            return 2; // Nuit
        }
        
        private int GetPolicePresence()
        {
            var playerWanted = Game.Player.WantedLevel;
            var nearbyPolice = World.GetNearbyPeds(Game.Player.Character.Position, 100.0f)
                .Count(p => p.RelationshipGroup == RelationshipGroup.Cop);
            
            return Math.Min(10, playerWanted * 2 + nearbyPolice);
        }
        
        private string GetTimeContext()
        {
            var hour = DateTime.Now.Hour;
            if (hour >= 6 && hour <= 9) return "morning_rush";
            if (hour >= 10 && hour <= 16) return "business_hours";
            if (hour >= 17 && hour <= 19) return "evening_rush";
            if (hour >= 20 && hour <= 23) return "night_life";
            return "night_quiet";
        }
        
        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            // Raccourcis clavier pour tests
            if (e.KeyCode == Keys.F7)
            {
                UI.Notify("~g~Création de nouveaux PNJ IA...");
                Task.Run(async () => await SpawnNewNpc());
            }
            
            if (e.KeyCode == Keys.F8)
            {
                UI.Notify("~b~Mise à jour des décisions IA...");
                Task.Run(async () => await UpdateNpcDecisions());
            }
            
            if (e.KeyCode == Keys.F9)
            {
                UI.Notify($"~y~PNJ gérés: {managedNpcs.Count}");
                LogMessage($"Statistiques: {managedNpcs.Count} PNJ actifs");
            }
        }
        
        private void LogMessage(string message)
        {
            var logEntry = $"[{DateTime.Now:HH:mm:ss}] {message}";
            Console.WriteLine(logEntry);
            
            // Écrire dans un fichier log
            try
            {
                var logPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), 
                    "LivingLosSantosAI.log");
                File.AppendAllText(logPath, logEntry + Environment.NewLine);
            }
            catch
            {
                // Ignorer les erreurs de logging
            }
        }
        
        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                httpClient?.Dispose();
                LogMessage("Système Living Los Santos AI arrêté");
            }
            base.Dispose(disposing);
        }
    }
}