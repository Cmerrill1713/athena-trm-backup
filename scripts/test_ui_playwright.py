#!/usr/bin/env python3
"""
Playwright-based UI testing and debugging
Tests the actual browser interaction with the chat UI
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_simple_chat():
    """Test simple-chat.html UI"""
    print("🧪 Testing Simple Chat UI with Playwright...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"  Browser console: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"  Browser error: {exc}"))
        
        try:
            # Navigate to simple chat
            print("\n1. Loading simple-chat.html...")
            await page.goto("http://localhost:8080/simple-chat.html")
            await page.wait_for_load_state("networkidle")
            
            # Check connection status
            print("\n2. Checking connection status...")
            status_text = await page.locator("#status").inner_text()
            print(f"   Status: {status_text}")
            
            # Type a message
            print("\n3. Typing test message...")
            await page.locator("#input").fill("Hello, test message")
            
            # Click send
            print("\n4. Clicking Send button...")
            await page.locator("button:has-text('Send')").click()
            
            # Wait for response (max 30 seconds)
            print("\n5. Waiting for response...")
            try:
                await page.wait_for_selector(".assistant", timeout=30000)
                
                # Get the response
                assistant_messages = await page.locator(".assistant").all()
                if assistant_messages:
                    response_text = await assistant_messages[-1].inner_text()
                    print(f"\n✅ SUCCESS! Got response:")
                    print(f"   {response_text[:200]}...")
                    return True
                else:
                    print("\n❌ FAILED: No assistant message found")
                    return False
                    
            except Exception as e:
                print(f"\n❌ FAILED: Timeout waiting for response")
                print(f"   Error: {e}")
                
                # Take screenshot
                await page.screenshot(path="logs/ui-error-simple.png")
                print("   Screenshot saved to logs/ui-error-simple.png")
                
                # Get page content for debugging
                content = await page.content()
                with open("logs/ui-error-simple.html", "w") as f:
                    f.write(content)
                print("   Page HTML saved to logs/ui-error-simple.html")
                
                return False
                
        finally:
            await browser.close()

async def test_athena_chat():
    """Test athena-chat.html UI"""
    print("\n\n🧪 Testing Athena Chat UI with Playwright...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"  Browser error: {exc}"))
        
        try:
            # Navigate to athena chat
            print("\n1. Loading athena-chat.html...")
            await page.goto("http://localhost:8080/athena-chat.html")
            await page.wait_for_load_state("networkidle")
            
            # Wait for connection
            print("\n2. Waiting for connection...")
            await page.wait_for_selector(".status.connected", timeout=10000)
            status_text = await page.locator(".status").inner_text()
            print(f"   Status: {status_text}")
            
            # Type a message
            print("\n3. Typing test message...")
            await page.locator("#input").fill("Hello, this is a test")
            
            # Click send
            print("\n4. Clicking Send button...")
            await page.locator("#send").click()
            
            # Wait for typing indicator to appear
            print("\n5. Waiting for response...")
            await asyncio.sleep(2)
            
            # Check for response
            try:
                # Wait for a message that's not just "thinking"
                await page.wait_for_function("""
                    () => {
                        const messages = document.querySelectorAll('.message.assistant');
                        if (messages.length === 0) return false;
                        const lastMsg = messages[messages.length - 1];
                        const text = lastMsg.innerText;
                        return text.length > 20 && !text.includes('typing');
                    }
                """, timeout=30000)
                
                # Get the response
                assistant_messages = await page.locator(".message.assistant").all()
                if assistant_messages:
                    response_text = await assistant_messages[-1].inner_text()
                    print(f"\n✅ SUCCESS! Got response:")
                    print(f"   {response_text[:200]}...")
                    
                    # Print console logs
                    print("\n📋 Browser console logs:")
                    for log in console_logs[-10:]:
                        print(f"   {log}")
                    
                    return True
                else:
                    print("\n❌ FAILED: No assistant message found")
                    print("\n📋 All console logs:")
                    for log in console_logs:
                        print(f"   {log}")
                    return False
                    
            except Exception as e:
                print(f"\n❌ FAILED: Timeout or error waiting for response")
                print(f"   Error: {e}")
                
                # Print console logs for debugging
                print("\n📋 Browser console logs:")
                for log in console_logs:
                    print(f"   {log}")
                
                # Take screenshot
                await page.screenshot(path="logs/ui-error-athena.png")
                print("\n   Screenshot saved to logs/ui-error-athena.png")
                
                # Get page content
                content = await page.content()
                with open("logs/ui-error-athena.html", "w") as f:
                    f.write(content)
                print("   Page HTML saved to logs/ui-error-athena.html")
                
                # Get chat container content
                chat_html = await page.locator("#chat").inner_html()
                print(f"\n   Chat container HTML:")
                print(f"   {chat_html[:500]}...")
                
                return False
                
        finally:
            # Keep browser open for inspection
            print("\n⏳ Keeping browser open for 10 seconds for inspection...")
            await asyncio.sleep(10)
            await browser.close()

async def main():
    """Run all UI tests"""
    print("═══════════════════════════════════════════════════════════════════════")
    print("  PLAYWRIGHT UI TESTING & DEBUGGING")
    print("═══════════════════════════════════════════════════════════════════════")
    
    # Test simple chat first
    simple_result = await test_simple_chat()
    
    # Test athena chat
    athena_result = await test_athena_chat()
    
    # Summary
    print("\n\n═══════════════════════════════════════════════════════════════════════")
    print("  TEST SUMMARY")
    print("═══════════════════════════════════════════════════════════════════════")
    print(f"\nSimple Chat: {'✅ PASS' if simple_result else '❌ FAIL'}")
    print(f"Athena Chat: {'✅ PASS' if athena_result else '❌ FAIL'}")
    
    if not simple_result or not athena_result:
        print("\n📋 Check logs/ui-error-*.png and logs/ui-error-*.html for details")
    
    return simple_result and athena_result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)


