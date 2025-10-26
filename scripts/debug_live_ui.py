#!/usr/bin/env python3
"""
Debug live UI by connecting to existing browser
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_existing_ui():
    """Connect to existing browser and debug"""
    print("🔍 Connecting to existing browser to debug UI...")
    
    async with async_playwright() as p:
        # Connect to existing browser on debugging port
        try:
            # Launch with remote debugging
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Connected to existing browser")
        except Exception as e:
            print(f"❌ Could not connect to existing browser: {e}")
            print("\n📋 Alternative: Launch new browser with debugging enabled")
            browser = await p.chromium.launch(
                headless=False,
                args=['--remote-debugging-port=9222']
            )
        
        # Get all contexts and pages
        contexts = browser.contexts
        print(f"\n📊 Found {len(contexts)} browser contexts")
        
        for ctx_idx, context in enumerate(contexts):
            pages = context.pages
            print(f"\n  Context {ctx_idx}: {len(pages)} pages")
            
            for page_idx, page in enumerate(pages):
                url = page.url
                print(f"    Page {page_idx}: {url}")
                
                # Check if this is our chat UI
                if 'localhost:8080' in url and ('chat' in url or url.endswith('8080/')):
                    print(f"\n🎯 Found chat UI: {url}")
                    await debug_page(page)
        
        print("\n⏳ Keeping browser connection open...")
        await asyncio.sleep(5)

async def debug_page(page):
    """Debug a specific page"""
    print("\n🔍 Debugging page...")
    
    # Get page title
    title = await page.title()
    print(f"  Title: {title}")
    
    # Check for chat container
    try:
        chat = await page.query_selector("#chat")
        if chat:
            print("  ✅ Found #chat container")
            
            # Get chat HTML
            chat_html = await chat.inner_html()
            print(f"  Chat HTML length: {len(chat_html)}")
            
            if len(chat_html) > 100:
                print(f"  Chat content preview: {chat_html[:200]}...")
            else:
                print(f"  Chat content: {chat_html}")
        else:
            print("  ❌ No #chat container found")
    except Exception as e:
        print(f"  ⚠️  Error checking chat: {e}")
    
    # Check for input
    try:
        input_elem = await page.query_selector("#input")
        if input_elem:
            print("  ✅ Found #input field")
            value = await input_elem.input_value()
            print(f"  Input value: '{value}'")
        else:
            print("  ❌ No #input field found")
    except Exception as e:
        print(f"  ⚠️  Error checking input: {e}")
    
    # Check for status
    try:
        status = await page.query_selector("#status, .status")
        if status:
            status_text = await status.inner_text()
            print(f"  Status: {status_text}")
        else:
            print("  ⚠️  No status element found")
    except Exception as e:
        print(f"  ⚠️  Error checking status: {e}")
    
    # Get console logs
    print("\n📋 Setting up console listener...")
    logs = []
    
    def handle_console(msg):
        logs.append(f"{msg.type}: {msg.text}")
        print(f"  Console: {msg.type}: {msg.text}")
    
    page.on("console", handle_console)
    
    # Try to send a message
    print("\n🧪 Testing message send...")
    try:
        # Fill input
        await page.fill("#input", "Test from Playwright")
        print("  ✅ Filled input")
        
        # Click send button
        await page.click("button:has-text('Send'), #send")
        print("  ✅ Clicked send button")
        
        # Wait and check for response
        print("  ⏳ Waiting 10 seconds for response...")
        await asyncio.sleep(10)
        
        # Check for new messages
        messages = await page.query_selector_all(".message, .assistant")
        print(f"  Found {len(messages)} message elements")
        
        if messages:
            last_msg = messages[-1]
            text = await last_msg.inner_text()
            print(f"  Last message: {text[:200]}...")
        
    except Exception as e:
        print(f"  ❌ Error during test: {e}")
    
    print("\n📋 Recent console logs:")
    for log in logs[-10:]:
        print(f"  {log}")

if __name__ == "__main__":
    asyncio.run(debug_existing_ui())


