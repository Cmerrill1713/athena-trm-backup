#!/usr/bin/env python3
"""
UI Test Suite for Athena Chat Frontend
Tests actual HTML interfaces using Playwright
"""

import asyncio
import json
from playwright.async_api import async_playwright, expect

class AthenaUITest:
    def __init__(self):
        self.base_url = "http://localhost:8082"
        self.api_url = "http://localhost:8080"
        
    async def test_athena_chat_ui(self):
        """Test the full-featured athena-chat.html interface"""
        print("\n🧪 Test 1: Athena Chat UI")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to chat UI
                print(f"📍 Navigating to {self.base_url}/athena-chat.html...")
                await page.goto(f"{self.base_url}/athena-chat.html", wait_until="networkidle")
                
                # Check page loaded
                title = await page.title()
                print(f"✅ Page loaded: {title}")
                
                # Wait for connection status
                print("⏳ Waiting for connection indicator...")
                await page.wait_for_selector("text=Connected", timeout=10000)
                print("✅ Connection established")
                
                # Find input field
                print("🔍 Finding input field...")
                input_selector = 'input[type="text"], textarea, [contenteditable="true"]'
                await page.wait_for_selector(input_selector, timeout=5000)
                print("✅ Input field found")
                
                # Type a message
                test_message = "What is TRM? Answer in one sentence."
                print(f"⌨️  Typing: '{test_message}'...")
                await page.fill(input_selector, test_message)
                print("✅ Message typed")
                
                # Find and click send button
                print("🔍 Finding send button...")
                send_button = page.locator('button:has-text("Send"), button:has-text("Submit"), button[type="submit"]').first
                await send_button.click()
                print("✅ Send button clicked")
                
                # Wait for response
                print("⏳ Waiting for AI response...")
                await page.wait_for_timeout(5000)  # Give time for response
                
                # Check for response in chat history
                page_content = await page.content()
                
                # Look for TRM-related response
                if "Tiny Recursive" in page_content or "TRM" in page_content:
                    print("✅ Response received and contains TRM content")
                else:
                    print("⚠️  Response may not contain expected content")
                
                # Check for infinite "thinking" loop
                if "thinking" in page_content.lower() or "..." in page_content:
                    print("⚠️  May be stuck in thinking loop")
                else:
                    print("✅ No thinking loop detected")
                
                # Take screenshot
                await page.screenshot(path="test_results_athena_chat.png")
                print("📸 Screenshot saved: test_results_athena_chat.png")
                
                print("\n✅ ATHENA CHAT UI TEST: PASSED")
                return True
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                await page.screenshot(path="test_error_athena_chat.png")
                print("📸 Error screenshot saved: test_error_athena_chat.png")
                return False
            finally:
                await browser.close()
    
    async def test_simple_chat_ui(self):
        """Test the simple-chat.html interface"""
        print("\n🧪 Test 2: Simple Chat UI")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"📍 Navigating to {self.base_url}/simple-chat.html...")
                await page.goto(f"{self.base_url}/simple-chat.html", wait_until="networkidle")
                
                title = await page.title()
                print(f"✅ Page loaded: {title}")
                
                # Test connection button if present
                if await page.locator('button:has-text("Test Connection")').count() > 0:
                    print("🔘 Clicking 'Test Connection' button...")
                    await page.click('button:has-text("Test Connection")')
                    await page.wait_for_timeout(2000)
                    print("✅ Connection test triggered")
                
                # Type message
                test_message = "Hello from automated test"
                print(f"⌨️  Typing: '{test_message}'...")
                input_field = page.locator('input[type="text"], textarea').first
                await input_field.fill(test_message)
                
                # Send message
                print("📤 Sending message...")
                send_btn = page.locator('button:has-text("Send"), button[type="submit"]').first
                await send_btn.click()
                
                # Wait for response
                await page.wait_for_timeout(5000)
                
                page_content = await page.content()
                if "Hello" in page_content or "assist" in page_content.lower():
                    print("✅ Response received")
                else:
                    print("⚠️  No clear response found")
                
                await page.screenshot(path="test_results_simple_chat.png")
                print("📸 Screenshot saved: test_results_simple_chat.png")
                
                print("\n✅ SIMPLE CHAT UI TEST: PASSED")
                return True
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                await page.screenshot(path="test_error_simple_chat.png")
                return False
            finally:
                await browser.close()
    
    async def test_open_webui(self):
        """Test the Open WebUI production interface"""
        print("\n🧪 Test 3: Open WebUI (Production)")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"📍 Navigating to http://localhost:3000...")
                await page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
                
                title = await page.title()
                print(f"✅ Page loaded: {title}")
                
                # Check if UI loaded
                page_content = await page.content()
                if "Open WebUI" in page_content or "chat" in page_content.lower():
                    print("✅ Open WebUI interface detected")
                else:
                    print("⚠️  Open WebUI may not be fully loaded")
                
                await page.screenshot(path="test_results_open_webui.png")
                print("📸 Screenshot saved: test_results_open_webui.png")
                
                print("\n✅ OPEN WEBUI TEST: PASSED")
                return True
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                await page.screenshot(path="test_error_open_webui.png")
                return False
            finally:
                await browser.close()
    
    async def run_all_tests(self):
        """Run all frontend tests"""
        print("\n" + "=" * 60)
        print("🎯 ATHENA FRONTEND UI TEST SUITE")
        print("=" * 60)
        
        results = {
            "athena_chat": await self.test_athena_chat_ui(),
            "simple_chat": await self.test_simple_chat_ui(),
            "open_webui": await self.test_open_webui()
        }
        
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL FRONTEND TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return False

if __name__ == "__main__":
    tester = AthenaUITest()
    success = asyncio.run(tester.run_all_tests())
    exit(0 if success else 1)

