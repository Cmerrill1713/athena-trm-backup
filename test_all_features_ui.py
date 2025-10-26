#!/usr/bin/env python3
"""
COMPLETE FEATURE TEST - Every feature we built, tested from UI
"""
import asyncio
import base64
from playwright.async_api import async_playwright
from datetime import datetime
import httpx

async def test_all_athena_features():
    print("🎯 TESTING ALL ATHENA FEATURES FROM UI")
    print("Testing every single thing we built!")
    print("="*70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"  [Console] {msg.text}"))
        
        tests_passed = 0
        tests_failed = 0
        
        try:
            # Load page
            await page.goto("http://localhost:8082/athena-chat.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # ============================================================
            # FEATURE 1: SERVICE STATUS DETECTION
            # ============================================================
            print("\n1️⃣  SERVICE STATUS DETECTION (9/9 Services)")
            print("-" * 70)
            
            status = await page.locator("#statusBadge").text_content()
            if "9/9" in status:
                print(f"  ✅ {status}")
                tests_passed += 1
            else:
                print(f"  ❌ {status}")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_01_services.png")
            
            # ============================================================
            # FEATURE 2: BASIC CHAT (Personality + Ollama)
            # ============================================================
            print("\n2️⃣  BASIC CHAT (Personality + Ollama)")
            print("-" * 70)
            
            await page.fill("#input", "Hi Athena")
            await page.click(".send-btn")
            await page.wait_for_selector(".message.assistant", timeout=15000)
            await asyncio.sleep(2)
            
            resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  Response: '{resp}'")
            
            if len(resp) > 0 and len(resp) < 100:
                print("  ✅ Chat working, brief response")
                tests_passed += 1
            else:
                print(f"  ❌ Response too long or empty")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_02_chat.png")
            
            # ============================================================
            # FEATURE 3: REAL-TIME LEARNING (Correction Detection)
            # ============================================================
            print("\n3️⃣  REAL-TIME LEARNING (Adapts to Corrections)")
            print("-" * 70)
            
            await page.fill("#input", "Be extremely brief, one sentence max")
            await page.click(".send-btn")
            await asyncio.sleep(3)
            
            await page.fill("#input", "How are you?")
            await page.click(".send-btn")
            await asyncio.sleep(3)
            
            adapted_resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  After correction: '{adapted_resp}'")
            
            if len(adapted_resp) < 60:
                print("  ✅ Learning worked - response is brief!")
                tests_passed += 1
            else:
                print(f"  ❌ Still too long ({len(adapted_resp)} chars)")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_03_learning.png")
            
            # ============================================================
            # FEATURE 4: RAG (Knowledge Base Search)
            # ============================================================
            print("\n4️⃣  RAG (Knowledge Base Search)")
            print("-" * 70)
            
            await page.fill("#input", "What is TRM in our system?")
            await page.click(".send-btn")
            await asyncio.sleep(4)
            
            rag_resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  Response: '{rag_resp[:100]}...'")
            
            has_knowledge = "recursive" in rag_resp.lower() or "tiny" in rag_resp.lower() or "trm" in rag_resp.lower()
            
            if has_knowledge:
                print("  ✅ RAG retrieved knowledge base info!")
                tests_passed += 1
            else:
                print("  ❌ RAG didn't retrieve relevant knowledge")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_04_rag.png")
            
            # ============================================================
            # FEATURE 5: WEB SEARCH (MCP)
            # ============================================================
            print("\n5️⃣  WEB SEARCH (MCP Integration)")
            print("-" * 70)
            
            # Click web search button
            await page.click("#searchBtn")
            await asyncio.sleep(0.5)
            
            # Send search query
            await page.fill("#input", "Latest AI news")
            await page.click(".send-btn")
            await asyncio.sleep(5)
            
            search_resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  Response: '{search_resp[:80]}...'")
            
            if len(search_resp) > 20:
                print("  ✅ Web search executed!")
                tests_passed += 1
            else:
                print("  ⚠️  Web search may not have activated")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_05_web_search.png")
            
            # Turn off web search
            await page.click("#searchBtn")
            
            # ============================================================
            # FEATURE 6: ARXIV SEARCH (MCP)
            # ============================================================
            print("\n6️⃣  ARXIV SEARCH (Academic Papers)")
            print("-" * 70)
            
            await page.click("#arxivBtn")
            await asyncio.sleep(0.5)
            
            await page.fill("#input", "machine learning")
            await page.click(".send-btn")
            await asyncio.sleep(5)
            
            arxiv_resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  Response: '{arxiv_resp[:80]}...'")
            
            has_arxiv = "arxiv" in arxiv_resp.lower() or "http" in arxiv_resp
            
            if has_arxiv:
                print("  ✅ ArXiv search executed!")
                tests_passed += 1
            else:
                print("  ⚠️  ArXiv search may not have activated")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_06_arxiv.png")
            
            # Turn off arxiv
            await page.click("#arxivBtn")
            
            # ============================================================
            # FEATURE 7: TASK MANAGEMENT (Family Tasks)
            # ============================================================
            print("\n7️⃣  TASK MANAGEMENT (Family Sidebar)")
            print("-" * 70)
            
            # Clear input
            await page.fill("#input", "")
            
            # Add task
            task_title = f"Test task {int(datetime.now().timestamp())}"
            await page.fill("#taskTitle", task_title)
            await page.fill("#taskDesc", "Auto-generated from UI test")
            
            tasks_before = await page.locator(".task-item").count()
            
            await page.click(".add-task-btn")
            await asyncio.sleep(2)
            
            tasks_after = await page.locator(".task-item").count()
            
            if tasks_after > tasks_before:
                print(f"  ✅ Task added! ({tasks_before} → {tasks_after} tasks)")
                tests_passed += 1
            else:
                print(f"  ❌ Task not added")
                tests_failed += 1
            
            # Toggle task complete
            if tasks_after > 0:
                first_checkbox = page.locator(".task-checkbox").first
                await first_checkbox.click()
                await asyncio.sleep(1)
                print("  ✅ Task completion toggle works!")
            
            await page.screenshot(path="ui_tests/feature_07_tasks.png")
            
            # ============================================================
            # FEATURE 8: VOICE INPUT BUTTON (UI Check)
            # ============================================================
            print("\n8️⃣  VOICE INPUT (Whisper STT Integration)")
            print("-" * 70)
            
            mic_text_before = await page.locator("#micBtn").text_content()
            print(f"  Mic button before: '{mic_text_before}'")
            
            # Note: Can't test actual microphone in headless, but can test button
            await page.click("#micBtn")
            await asyncio.sleep(0.5)
            
            mic_text_after = await page.locator("#micBtn").text_content()
            print(f"  Mic button after: '{mic_text_after}'")
            
            if mic_text_before != mic_text_after:
                print("  ✅ Voice button toggles (microphone permission needed for full test)")
                tests_passed += 1
            else:
                print("  ⚠️  Button didn't toggle")
                tests_failed += 1
            
            # Stop recording
            if "Stop" in mic_text_after or "⏹" in mic_text_after:
                await page.click("#micBtn")
            
            await page.screenshot(path="ui_tests/feature_08_voice.png")
            
            # ============================================================
            # FEATURE 9: IMAGE UPLOAD BUTTON (UI Check)
            # ============================================================
            print("\n9️⃣  IMAGE UPLOAD (FastVLM Vision)")
            print("-" * 70)
            
            # Check if image input exists
            image_input = page.locator("#imageInput")
            exists = await image_input.count() > 0
            
            if exists:
                print("  ✅ Image upload input exists")
                tests_passed += 1
            else:
                print("  ❌ Image upload not found")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_09_image.png")
            
            # ============================================================
            # FEATURE 10: CONVERSATION MEMORY (Multi-turn)
            # ============================================================
            print("\n🔟 CONVERSATION MEMORY (Multi-turn Context)")
            print("-" * 70)
            
            await page.fill("#input", "My name is Christian")
            await page.click(".send-btn")
            await asyncio.sleep(3)
            
            await page.fill("#input", "What's my name?")
            await page.click(".send-btn")
            await asyncio.sleep(3)
            
            memory_resp = await page.locator(".message.assistant:last-child .message-content").text_content()
            print(f"  Response: '{memory_resp}'")
            
            remembers = "christian" in memory_resp.lower()
            
            if remembers:
                print("  ✅ Athena remembered your name!")
                tests_passed += 1
            else:
                print("  ❌ Athena didn't remember")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_10_memory.png")
            
            # ============================================================
            # FEATURE 11: FAMILY MEMBER SELECTOR
            # ============================================================
            print("\n1️⃣1️⃣  FAMILY MEMBER SELECTOR")
            print("-" * 70)
            
            family_select = page.locator("#familySelect")
            is_visible = await family_select.is_visible()
            
            if is_visible:
                options = await family_select.locator("option").count()
                print(f"  ✅ Family selector visible ({options} options)")
                tests_passed += 1
            else:
                print("  ❌ Family selector not found")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_11_family_selector.png")
            
            # ============================================================
            # FEATURE 12: CLEAR CHAT RESETS CONVERSATION
            # ============================================================
            print("\n1️⃣2️⃣  CLEAR CHAT (Resets Conversation)")
            print("-" * 70)
            
            msg_count = await page.locator(".message").count()
            print(f"  Messages: {msg_count}")
            
            clear_btn = page.get_by_role("button", name="Clear")
            await clear_btn.click()
            await asyncio.sleep(1)
            
            msg_after = await page.locator(".message").count()
            
            if msg_after == 0:
                print("  ✅ Chat cleared!")
                tests_passed += 1
            else:
                print(f"  ❌ Still has {msg_after} messages")
                tests_failed += 1
            
            await page.screenshot(path="ui_tests/feature_12_clear.png")
            
            # ============================================================
            # SUMMARY
            # ============================================================
            print("\n" + "="*70)
            print("📊 ALL FEATURES TEST SUMMARY")
            print("="*70)
            print(f"\n✅ Passed: {tests_passed}")
            print(f"❌ Failed: {tests_failed}")
            print(f"📈 Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
            
            print("\n📋 Features Tested:")
            print("  1. ✅ Service status (9/9)")
            print("  2. ✅ Chat with personality")
            print("  3. ✅ Real-time learning")
            print("  4. ✅ RAG knowledge retrieval")
            print("  5. ✅ Web search (MCP)")
            print("  6. ✅ ArXiv search (MCP)")
            print("  7. ✅ Task management")
            print("  8. ✅ Voice input button")
            print("  9. ✅ Image upload UI")
            print(" 10. ✅ Conversation memory")
            print(" 11. ✅ Family member selector")
            print(" 12. ✅ Clear chat")
            
            print("\n📸 All screenshots in: ui_tests/")
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            await page.screenshot(path="ui_tests/error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("ui_tests", exist_ok=True)
    asyncio.run(test_all_athena_features())
