#!/usr/bin/env python3
"""
COMPREHENSIVE ATHENA SYSTEM TEST
Tests ALL features from frontend perspective
Ensures all hard work is actually functioning
"""
import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from datetime import datetime
import base64
import os

class AthenaSystemTest:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "failures": [],
            "passed": 0,
            "failed": 0
        }
    
    def log(self, test_name, status, details=""):
        """Log test result"""
        emoji = "✅" if status else "❌"
        print(f"{emoji} {test_name}: {details if details else ('PASS' if status else 'FAIL')}")
        
        self.results["tests"][test_name] = {
            "status": "PASS" if status else "FAIL",
            "details": details
        }
        
        if status:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["failures"].append(test_name)
    
    async def test_all_services(self):
        """TEST 1: All 9 Services Health"""
        print("\n" + "="*60)
        print("TEST 1: ALL 9 SERVICES HEALTH")
        print("="*60)
        
        services = {
            'UAI': 'http://localhost:8080/health',
            'Router': 'http://localhost:9113/health',
            'MCP': 'http://localhost:8412/health',
            'Whisper': 'http://localhost:8095/health',
            'Kokoro': 'http://localhost:8091/health',
            'FastVLM': 'http://localhost:8088/health',
            'Judicial': 'http://localhost:8096/v2/health',
            'Learning': 'http://localhost:8098/health',
            'macOS Bridge': 'http://localhost:8099/health'
        }
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            for name, url in services.items():
                try:
                    resp = await client.get(url)
                    self.log(f"Service: {name}", resp.status_code == 200, f"port {url.split(':')[2].split('/')[0]}")
                except Exception as e:
                    self.log(f"Service: {name}", False, str(e))
    
    async def test_chat_personality(self):
        """TEST 2: Athena's Personality (Brief & Warm)"""
        print("\n" + "="*60)
        print("TEST 2: ATHENA'S PERSONALITY")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Test simple greeting
            resp = await client.post(
                "http://localhost:8080/v1/chat/completions",
                json={"user_id": "test_personality", "messages": [{"role": "user", "content": "Hi"}]}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                response_text = data["choices"][0]["message"]["content"]
                is_brief = len(response_text) < 80
                
                print(f"  Response: '{response_text}'")
                self.log("Chat: Brief response", is_brief, f"{len(response_text)} chars")
                self.log("Chat: Contains emoji", "😊" in response_text or "👋" in response_text or "✨" in response_text)
            else:
                self.log("Chat: Basic response", False, f"HTTP {resp.status_code}")
    
    async def test_realtime_learning(self):
        """TEST 3: Real-Time Learning (Immediate Adaptation)"""
        print("\n" + "="*60)
        print("TEST 3: REAL-TIME LEARNING")
        print("="*60)
        
        user_id = f"test_learning_{int(datetime.now().timestamp())}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Normal response
            resp1 = await client.post(
                "http://localhost:8080/v1/chat/completions",
                json={"user_id": user_id, "messages": [{"role": "user", "content": "Hello"}]}
            )
            
            # Step 2: Send correction
            resp2 = await client.post(
                "http://localhost:8080/v1/chat/completions",
                json={
                    "user_id": user_id,
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hello! How are you?"},
                        {"role": "user", "content": "Be extremely casual, like texting"}
                    ]
                }
            )
            
            if resp2.status_code == 200:
                data2 = resp2.json()
                correction_saved = data2["_athena"].get("correction_saved_to_db", False)
                self.log("Learning: Correction detected", correction_saved)
            
            # Step 3: Test if adaptation persisted
            await asyncio.sleep(1)
            resp3 = await client.post(
                "http://localhost:8080/v1/chat/completions",
                json={
                    "user_id": user_id,
                    "messages": [
                        {"role": "user", "content": "What's up?"}
                    ]
                }
            )
            
            if resp3.status_code == 200:
                data3 = resp3.json()
                learned_active = data3["_athena"].get("permanent_learning_active", False)
                response3 = data3["choices"][0]["message"]["content"]
                
                print(f"  After correction: '{response3}'")
                self.log("Learning: Preference loaded", learned_active)
                self.log("Learning: Response adapted", len(response3) < 60, f"{len(response3)} chars")
    
    async def test_permanent_storage(self):
        """TEST 4: Permanent Storage (PostgreSQL)"""
        print("\n" + "="*60)
        print("TEST 4: PERMANENT STORAGE (DATABASE)")
        print("="*60)
        
        # Check database has preferences
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "athena-postgres", "psql", "-U", "athena", "-d", "athena",
             "-c", "SELECT COUNT(*) FROM user_preferences;"],
            capture_output=True,
            text=True
        )
        
        if "0 rows" not in result.stdout and result.returncode == 0:
            count_line = [line for line in result.stdout.split('\n') if line.strip() and line.strip().isdigit()]
            if count_line:
                count = int(count_line[0].strip())
                self.log("Database: Preferences stored", count > 0, f"{count} users")
        else:
            self.log("Database: Preferences stored", False)
    
    async def test_rag_system(self):
        """TEST 5: RAG System (Semantic Search)"""
        print("\n" + "="*60)
        print("TEST 5: RAG SYSTEM (KNOWLEDGE RETRIEVAL)")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Ask something that should trigger RAG
            resp = await client.post(
                "http://localhost:8080/v1/chat/completions",
                json={
                    "user_id": "test_rag",
                    "messages": [{"role": "user", "content": "What is TRM in our system?"}]
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                rag_used = data["_athena"].get("rag_enabled", False)
                response = data["choices"][0]["message"]["content"]
                
                has_trm_knowledge = "tiny recursive" in response.lower() or "recursive model" in response.lower()
                
                self.log("RAG: Search activated", rag_used)
                self.log("RAG: Knowledge retrieved", has_trm_knowledge, "TRM definition found")
            else:
                self.log("RAG: System working", False)
    
    async def test_multimodal_services(self):
        """TEST 6: Multimodal Services (Vision, Voice, Speech)"""
        print("\n" + "="*60)
        print("TEST 6: MULTIMODAL SERVICES")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test FastVLM (Vision)
            try:
                resp = await client.get("http://localhost:8088/health")
                self.log("Multimodal: FastVLM (Vision)", resp.status_code == 200)
            except:
                self.log("Multimodal: FastVLM (Vision)", False)
            
            # Test Kokoro (TTS)
            try:
                resp = await client.get("http://localhost:8091/health")
                self.log("Multimodal: Kokoro (TTS)", resp.status_code == 200)
            except:
                self.log("Multimodal: Kokoro (TTS)", False)
            
            # Test Whisper (STT)
            try:
                resp = await client.get("http://localhost:8095/health")
                self.log("Multimodal: Whisper (STT)", resp.status_code == 200)
            except:
                self.log("Multimodal: Whisper (STT)", False)
    
    async def test_macos_tools(self):
        """TEST 7: macOS Tools Integration"""
        print("\n" + "="*60)
        print("TEST 7: MACOS TOOLS")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test macOS Bridge health
            try:
                resp = await client.get("http://localhost:8099/health")
                if resp.status_code == 200:
                    data = resp.json()
                    tools_available = data.get("tools_available", 0)
                    self.log("macOS: Bridge running", True, f"{tools_available} tools")
                else:
                    self.log("macOS: Bridge running", False)
            except Exception as e:
                self.log("macOS: Bridge running", False, str(e))
            
            # Test MCP Ecosystem
            try:
                resp = await client.get("http://localhost:8412/health")
                if resp.status_code == 200:
                    data = resp.json()
                    tools = data.get("tools_available", 0)
                    self.log("macOS: MCP Ecosystem", True, f"{tools} tools")
                else:
                    self.log("macOS: MCP Ecosystem", False)
            except:
                self.log("macOS: MCP Ecosystem", False)
    
    async def test_asi_safety(self):
        """TEST 8: ASI Safety (Judicial Oversight)"""
        print("\n" + "="*60)
        print("TEST 8: ASI SAFETY (JUDICIAL OVERSIGHT)")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test Judicial service
            try:
                resp = await client.get("http://localhost:8096/v2/health")
                self.log("ASI Safety: Judicial running", resp.status_code == 200)
            except:
                self.log("ASI Safety: Judicial running", False)
            
            # Test Federation
            try:
                resp = await client.get("http://localhost:8097/federation/health")
                self.log("ASI Safety: Federation running", resp.status_code == 200)
            except:
                self.log("ASI Safety: Federation running", False, "Optional service")
    
    async def test_frontend_ui(self):
        """TEST 9: Frontend UI (Browser Test)"""
        print("\n" + "="*60)
        print("TEST 9: FRONTEND UI (BROWSER)")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Load page
                await page.goto("http://localhost:8082/athena-chat.html", timeout=10000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                
                # Check service count
                status_badge = await page.locator("#statusBadge").text_content()
                services_ready = "9/9" in status_badge
                self.log("UI: Service detection", services_ready, status_badge)
                
                # Test chat input
                await page.fill("#input", "Test message")
                input_value = await page.locator("#input").input_value()
                self.log("UI: Input field works", input_value == "Test message")
                
                # Test send button
                send_btn = page.locator(".send-btn")
                is_visible = await send_btn.is_visible()
                self.log("UI: Send button visible", is_visible)
                
                # Test task sidebar
                task_title = page.locator("#taskTitle")
                task_visible = await task_title.is_visible()
                self.log("UI: Task sidebar loaded", task_visible)
                
                await page.screenshot(path="screenshots/full_system_test.png")
                
            except Exception as e:
                self.log("UI: Page load", False, str(e))
            finally:
                await browser.close()
    
    async def test_task_api(self):
        """TEST 10: Task Management API"""
        print("\n" + "="*60)
        print("TEST 10: TASK MANAGEMENT")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Create task
            try:
                resp = await client.post(
                    "http://localhost:8080/api/tasks",
                    json={
                        "id": int(datetime.now().timestamp()),
                        "title": "System test task",
                        "description": "Auto-generated test",
                        "completed": False
                    }
                )
                self.log("Tasks: Create task", resp.status_code == 200)
            except Exception as e:
                self.log("Tasks: Create task", False, str(e))
            
            # List tasks
            try:
                resp = await client.get("http://localhost:8080/api/tasks")
                if resp.status_code == 200:
                    tasks = resp.json()
                    self.log("Tasks: List tasks", True, f"{len(tasks)} tasks")
                else:
                    self.log("Tasks: List tasks", False)
            except:
                self.log("Tasks: List tasks", False)
    
    async def test_conversation_flow(self):
        """TEST 11: Full Conversation Flow"""
        print("\n" + "="*60)
        print("TEST 11: CONVERSATION FLOW (END-TO-END)")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("http://localhost:8082/athena-chat.html", timeout=10000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                
                # Send message
                await page.fill("#input", "Hi Athena!")
                await page.click(".send-btn")
                await page.wait_for_selector(".message.assistant", timeout=15000)
                await asyncio.sleep(2)
                
                # Check response appeared
                messages = await page.locator(".message").count()
                self.log("Conversation: Message sent", messages >= 2, f"{messages} messages")
                
                # Get response text
                response_el = page.locator(".message.assistant:last-child .message-content")
                response = await response_el.text_content()
                self.log("Conversation: Response received", len(response) > 0, f"'{response[:50]}...'")
                
                # Test correction
                await page.fill("#input", "Be super brief")
                await page.click(".send-btn")
                await asyncio.sleep(3)
                
                # Check if next response is brief
                await page.fill("#input", "How are you?")
                await page.click(".send-btn")
                await asyncio.sleep(3)
                
                last_response_el = page.locator(".message.assistant:last-child .message-content")
                last_response = await last_response_el.text_content()
                
                is_brief = len(last_response) < 60
                self.log("Conversation: Adapted to correction", is_brief, f"{len(last_response)} chars")
                
            except Exception as e:
                self.log("Conversation: Flow test", False, str(e))
            finally:
                await browser.close()
    
    async def test_database_persistence(self):
        """TEST 12: Database Persistence"""
        print("\n" + "="*60)
        print("TEST 12: DATABASE PERSISTENCE")
        print("="*60)
        
        import subprocess
        
        # Check PostgreSQL is running
        result = subprocess.run(
            ["docker", "exec", "athena-postgres", "psql", "-U", "athena", "-d", "athena",
             "-c", "SELECT COUNT(*) FROM user_preferences;"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.log("Database: PostgreSQL running", True)
            
            # Check if preferences exist
            has_data = "0" not in result.stdout.split('\n')[2].strip()
            self.log("Database: Has user preferences", has_data)
        else:
            self.log("Database: PostgreSQL running", False)
    
    async def run_all_tests(self):
        """Run all tests"""
        print("\n🧪 COMPREHENSIVE ATHENA SYSTEM TEST")
        print("Testing ALL features to ensure hard work is functioning")
        print("")
        
        await self.test_all_services()
        await self.test_chat_personality()
        await self.test_realtime_learning()
        await self.test_permanent_storage()
        await self.test_rag_system()
        await self.test_multimodal_services()
        await self.test_macos_tools()
        await self.test_asi_safety()
        await self.test_frontend_ui()
        await self.test_task_api()
        await self.test_conversation_flow()
        await self.test_database_persistence()
        
        # Summary
        print("\n" + "="*60)
        print("📊 FINAL TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print(f"\n⚠️  Failed tests:")
            for failure in self.results['failures']:
                print(f"   - {failure}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Every feature we built is working! 💙")
        
        # Save results
        with open("comprehensive_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full results saved to: comprehensive_test_results.json")
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    
    tester = AthenaSystemTest()
    success = asyncio.run(tester.run_all_tests())
    
    exit(0 if success else 1)
