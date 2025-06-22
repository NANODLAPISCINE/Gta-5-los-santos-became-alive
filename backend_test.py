#!/usr/bin/env python3
import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

class GTA5AIPNJTester:
    def __init__(self, base_url="https://7c9a49cc-fad5-4687-bd9e-904acccadd50.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_npcs = []
        self.created_events = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data=None) -> Tuple[bool, Dict[str, Any]]:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        if success:
            print(f"API Version: {response.get('version')}")
            print(f"Status: {response.get('status')}")
        return success

    def test_create_npc(self, name: str, npc_type: str, location: Dict[str, Any]) -> str:
        """Create an NPC and return its ID if successful"""
        success, response = self.run_test(
            f"Create {npc_type.capitalize()} NPC",
            "POST",
            "npcs",
            200,
            data={
                "name": name,
                "npc_type": npc_type,
                "current_location": location
            }
        )
        
        if success and 'id' in response:
            npc_id = response['id']
            self.created_npcs.append(npc_id)
            print(f"Created NPC with ID: {npc_id}")
            return npc_id
        return None

    def test_get_all_npcs(self):
        """Test getting all NPCs"""
        success, response = self.run_test(
            "Get All NPCs",
            "GET",
            "npcs",
            200
        )
        
        if success:
            print(f"Found {len(response)} NPCs")
        return success

    def test_get_npc(self, npc_id: str):
        """Test getting a specific NPC"""
        success, response = self.run_test(
            "Get Specific NPC",
            "GET",
            f"npcs/{npc_id}",
            200
        )
        
        if success:
            print(f"NPC Name: {response.get('name')}")
            print(f"NPC Type: {response.get('npc_type')}")
        return success

    def test_update_npc(self, npc_id: str):
        """Test updating an NPC"""
        success, response = self.run_test(
            "Update NPC",
            "PUT",
            f"npcs/{npc_id}",
            200,
            data={
                "current_mood": "happy",
                "stress_level": 30
            }
        )
        
        if success:
            print(f"Updated NPC mood: {response.get('current_mood')}")
            print(f"Updated NPC stress: {response.get('stress_level')}")
        return success

    def test_npc_decision(self, npc_id: str):
        """Test making an NPC decision"""
        context = {
            "weather": "rainy",
            "traffic_density": 5,
            "police_presence": 2,
            "time_context": "night"
        }
        
        success, response = self.run_test(
            "NPC Decision",
            "POST",
            f"npcs/{npc_id}/decision",
            200,
            data=context
        )
        
        if success and 'decision' in response:
            print(f"Decision action: {response['decision'].get('action')}")
            print(f"Decision reasoning: {response['decision'].get('reasoning')}")
        return success

    def test_add_memory(self, npc_id: str):
        """Test adding a memory to an NPC"""
        memory_data = {
            "event_type": "interaction",
            "description": "Witnessed a car accident",
            "location": {
                "x": 100.0,
                "y": 200.0,
                "z": 10.0,
                "area_name": "Downtown Los Santos"
            },
            "importance": 8
        }
        
        success, response = self.run_test(
            "Add NPC Memory",
            "POST",
            f"npcs/{npc_id}/memory",
            200,
            data=memory_data
        )
        
        if success:
            print(f"Memory added: {response.get('message')}")
        return success

    def test_create_event(self):
        """Test creating a game event"""
        event_data = {
            "event_type": "crime",
            "description": "Armed robbery at convenience store",
            "location": {
                "x": 120.0,
                "y": 230.0,
                "z": 15.0,
                "area_name": "Little Seoul"
            },
            "participants": [],
            "severity": 8
        }
        
        success, response = self.run_test(
            "Create Game Event",
            "POST",
            "events",
            200,
            data=event_data
        )
        
        if success and 'event_id' in response:
            event_id = response['event_id']
            self.created_events.append(event_id)
            print(f"Created event with ID: {event_id}")
            print(f"Notified NPCs: {response.get('notified_npcs', 0)}")
        return success

    def test_get_events(self):
        """Test getting recent events"""
        success, response = self.run_test(
            "Get Recent Events",
            "GET",
            "events",
            200
        )
        
        if success:
            print(f"Found {len(response)} events")
        return success

    def test_get_stats(self):
        """Test getting system stats"""
        success, response = self.run_test(
            "Get System Stats",
            "GET",
            "stats",
            200
        )
        
        if success:
            print(f"Total NPCs: {response.get('total_npcs')}")
            print(f"Total Events: {response.get('total_events')}")
            print(f"System Status: {response.get('system_status')}")
        return success

    def test_create_sample_npcs(self):
        """Test creating sample NPCs"""
        success, response = self.run_test(
            "Create Sample NPCs",
            "POST",
            "npcs/create-sample",
            200
        )
        
        if success:
            print(f"Created {len(response.get('npcs', []))} sample NPCs")
        return success

    def test_daily_routine(self):
        """Test running daily routine"""
        success, response = self.run_test(
            "Run Daily Routine",
            "POST",
            "simulation/daily-routine",
            200
        )
        
        if success:
            print(f"Daily routine executed for {len(response.get('processed_npcs', []))} NPCs")
        return success

    def test_bulk_decisions(self):
        """Test bulk decisions"""
        if not self.created_npcs:
            print("No NPCs available for bulk decisions test")
            return False
            
        npc_contexts = []
        for npc_id in self.created_npcs[:2]:  # Use first 2 NPCs
            npc_contexts.append({
                "npc_id": npc_id,
                "context": {
                    "weather": "sunny",
                    "traffic_density": 8,
                    "police_presence": 1,
                    "time_context": "day"
                }
            })
        
        success, response = self.run_test(
            "Bulk Decisions",
            "POST",
            "simulation/bulk-decisions",
            200,
            data=npc_contexts
        )
        
        if success:
            print(f"Processed decisions for {len(response.get('results', []))} NPCs")
        return success

    def test_special_criminal_decision(self):
        """Special test: Criminal NPC decision at night with low police presence"""
        # Create a criminal NPC
        criminal_id = self.test_create_npc(
            f"Criminal_{datetime.now().strftime('%H%M%S')}",
            "criminal",
            {
                "x": -1393.0,
                "y": -584.0,
                "z": 30.0,
                "area_name": "Del Perro"
            }
        )
        
        if not criminal_id:
            print("Failed to create criminal NPC for special test")
            return False
            
        # Make a decision with night context and low police presence
        context = {
            "weather": "clear",
            "traffic_density": 2,
            "police_presence": 1,
            "time_context": "night"
        }
        
        success, response = self.run_test(
            "Criminal Night Decision",
            "POST",
            f"npcs/{criminal_id}/decision",
            200,
            data=context
        )
        
        if success and 'decision' in response:
            action = response['decision'].get('action')
            reasoning = response['decision'].get('reasoning')
            print(f"Criminal decision at night: {action}")
            print(f"Reasoning: {reasoning}")
            
            # Check if the decision is crime-related
            crime_related = any(term in action.lower() for term in ["crime", "steal", "rob", "hide"])
            if crime_related:
                print("✅ Criminal made a crime-related decision as expected")
            else:
                print("⚠️ Criminal did not make a crime-related decision")
        return success

    def test_memory_persistence(self, npc_id: str):
        """Special test: Memory persistence and influence on decisions"""
        # Add an important memory
        memory_data = {
            "event_type": "traumatic",
            "description": "Was robbed at gunpoint",
            "location": {
                "x": 100.0,
                "y": 200.0,
                "z": 10.0,
                "area_name": "Downtown Los Santos"
            },
            "importance": 9
        }
        
        success1 = self.test_add_memory(npc_id)
        if not success1:
            return False
            
        # Get the NPC to check if memory was added
        success2, npc_data = self.run_test(
            "Get NPC with Memory",
            "GET",
            f"npcs/{npc_id}",
            200
        )
        
        if success2:
            memories = npc_data.get('short_term_memory', [])
            print(f"NPC has {len(memories)} memories")
            if memories:
                print(f"Latest memory: {memories[-1].get('description')}")
        
        # Make a decision to see if memory influences it
        context = {
            "weather": "sunny",
            "traffic_density": 5,
            "police_presence": 3,
            "time_context": "day"
        }
        
        success3, response = self.run_test(
            "Decision After Memory",
            "POST",
            f"npcs/{npc_id}/decision",
            200,
            data=context
        )
        
        if success3 and 'decision' in response:
            print(f"Decision after memory: {response['decision'].get('action')}")
            print(f"Reasoning: {response['decision'].get('reasoning')}")
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 50)
        print("🚀 Starting GTA 5 AI NPC System Tests")
        print("=" * 50)
        
        # Basic API tests
        self.test_root_endpoint()
        
        # Create NPCs for testing
        civilian_id = self.test_create_npc(
            f"Civilian_{datetime.now().strftime('%H%M%S')}",
            "civilian",
            {
                "x": -1037.0,
                "y": -2738.0,
                "z": 20.0,
                "area_name": "Los Santos International Airport"
            }
        )
        
        police_id = self.test_create_npc(
            f"Officer_{datetime.now().strftime('%H%M%S')}",
            "police",
            {
                "x": 425.0,
                "y": -979.0,
                "z": 30.0,
                "area_name": "Mission Row Police Station"
            }
        )
        
        # NPC management tests
        self.test_get_all_npcs()
        
        if civilian_id:
            self.test_get_npc(civilian_id)
            self.test_update_npc(civilian_id)
            self.test_npc_decision(civilian_id)
            self.test_add_memory(civilian_id)
        
        # Event tests
        self.test_create_event()
        self.test_get_events()
        
        # Stats test
        self.test_get_stats()
        
        # Utility tests
        self.test_create_sample_npcs()
        
        # Simulation tests
        self.test_daily_routine()
        self.test_bulk_decisions()
        
        # Special tests
        self.test_special_criminal_decision()
        
        if civilian_id:
            self.test_memory_persistence(civilian_id)
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Tests completed: {self.tests_run}")
        print(f"✅ Tests passed: {self.tests_passed}")
        print(f"❌ Tests failed: {self.tests_run - self.tests_passed}")
        print("=" * 50)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = GTA5AIPNJTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)