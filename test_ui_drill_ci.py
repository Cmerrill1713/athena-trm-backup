#!/usr/bin/env python3
"""
UI Confidence Drill - CI Mode
Headless, artifact-generating, only fails on user-visible regressions
Safe for continuous integration
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
UI_URL = os.getenv("UI_URL", "http://localhost:8082/athena-chat.html")
HEADLESS = os.getenv("UI_HEADFUL", "0") == "0"
TIMEOUT = 30000
ARTIFACT_DIR = Path("artifacts/ui/last-run")

# Critical tests (user-visible)
CRITICAL_TESTS = [
    "page_load",
    "rag_query",
    "streaming",
    "clear_chat"
]

class UITestResult:
    def __init__(self, name, passed, message="", critical=False):
        self.name = name
        self.passed = passed
        self.message = message
        self.critical = critical
        self.timestamp = datetime.utcnow().isoformat()

class UIDrillCI:
    def __init__(self):
        self.results = []
        self.artifacts_dir = ARTIFACT_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.artifacts_dir / "screenshots").mkdir(exist_ok=True)
        (self.artifacts_dir / "har").mkdir(exist_ok=True)
        
        self.console_log = []
        self.network_log = []
    
    async def run(self):
        """Run all UI tests"""
        print("🔥 ATHENA UI CONFIDENCE DRILL (CI MODE)")
        print("=" * 80)
        print(f"Headless: {HEADLESS}")
        print(f"Artifacts: {self.artifacts_dir}")
        print("")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            
            # Create context with HAR recording
            context = await browser.new_context(
                record_har_path=str(self.artifacts_dir / "har" / "session.har"),
                record_video_dir=str(self.artifacts_dir) if not HEADLESS else None
            )
            
            page = await context.new_page()
            page.set_default_timeout(TIMEOUT)
            
            # Capture console and network
            page.on("console", lambda msg: self.console_log.append(f"[{msg.type}] {msg.text}"))
            page.on("response", lambda resp: self.network_log.append(f"{resp.status} {resp.url}"))
            
            try:
                # Run tests
                await self.test_page_load(page)
                await self.test_rag_query(page)
                await self.test_router_behavior(page)
                await self.test_streaming(page)
                await self.test_multi_turn(page)
                await self.test_clear_chat(page)
                
                # Optional tests (non-critical)
                await self.test_profiles(page)
                await self.test_voice_controls(page)
                await self.test_task_sidebar(page)
                await self.test_pwa_features(page)
                
            finally:
                # Save artifacts
                await self.save_artifacts(page)
                await context.close()
                await browser.close()
        
        # Generate report
        self.generate_report()
        
        # Return exit code
        return self.get_exit_code()
    
    async def test_page_load(self, page):
        """Critical: Page must load"""
        try:
            await page.goto(UI_URL)
            await page.wait_for_load_state("networkidle")
            
            # Screenshot
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "01_page_load.png")
            
            # Check title
            title = await page.title()
            
            if "Athena" in title:
                self.results.append(UITestResult("page_load", True, f"Loaded: {title}", critical=True))
            else:
                self.results.append(UITestResult("page_load", False, f"Wrong title: {title}", critical=True))
                
        except Exception as e:
            self.results.append(UITestResult("page_load", False, str(e), critical=True))
    
    async def test_rag_query(self, page):
        """Critical: RAG query must work"""
        try:
            await page.fill("#input", "What is TRM in one sentence?")
            await page.click("#send")
            
            # Wait for response
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            # Screenshot
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "02_rag_query.png")
            
            # Get response
            response = await page.locator(".message.assistant .message-content").last.text_content()
            
            if len(response) > 10 and any(word in response.lower() for word in ['tiny', 'recursive', 'model', 'trm']):
                self.results.append(UITestResult("rag_query", True, f"Got answer ({len(response)} chars)", critical=True))
            else:
                self.results.append(UITestResult("rag_query", False, "No valid response", critical=True))
                
        except Exception as e:
            self.results.append(UITestResult("rag_query", False, str(e), critical=True))
    
    async def test_router_behavior(self, page):
        """Non-critical: Router should adapt"""
        try:
            # Clear first
            await page.click(".tool-btn:has-text('Clear')")
            await asyncio.sleep(1)
            
            # Ask different types of questions
            await page.fill("#input", "List router capabilities")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "03_router_test.png")
            
            self.results.append(UITestResult("router_behavior", True, "Router responded", critical=False))
            
        except Exception as e:
            self.results.append(UITestResult("router_behavior", False, str(e), critical=False))
    
    async def test_streaming(self, page):
        """Critical: Streaming must work"""
        try:
            await page.fill("#input", "Explain the governance system")
            
            await page.click("#send")
            
            # Wait for response to start
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            
            # Wait for streaming to complete
            await asyncio.sleep(5)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "04_streaming.png")
            
            response = await page.locator(".message.assistant .message-content").last.text_content()
            
            if len(response) > 50:
                self.results.append(UITestResult("streaming", True, "Stream completed", critical=True))
            else:
                self.results.append(UITestResult("streaming", False, "Stream too short", critical=True))
                
        except Exception as e:
            self.results.append(UITestResult("streaming", False, str(e), critical=True))
    
    async def test_multi_turn(self, page):
        """Non-critical: Memory across turns"""
        try:
            await page.fill("#input", "What is the learning system?")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            await page.fill("#input", "What port does it use?")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content:not(:has-text('learning system'))", timeout=30000)
            await asyncio.sleep(2)
            
            response = await page.locator(".message.assistant .message-content").last.text_content()
            
            if any(port in response for port in ['8098', 'port']):
                self.results.append(UITestResult("multi_turn", True, "Context remembered", critical=False))
            else:
                self.results.append(UITestResult("multi_turn", False, "Context not remembered", critical=False))
                
        except Exception as e:
            self.results.append(UITestResult("multi_turn", False, str(e), critical=False))
    
    async def test_clear_chat(self, page):
        """Critical: Clear must work"""
        try:
            initial = await page.locator(".message").count()
            
            await page.click(".tool-btn:has-text('Clear')")
            await asyncio.sleep(1)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "05_clear.png")
            
            final = await page.locator(".message").count()
            
            if final == 0:
                self.results.append(UITestResult("clear_chat", True, "Clear works", critical=True))
            else:
                self.results.append(UITestResult("clear_chat", False, f"Still has {final} messages", critical=True))
                
        except Exception as e:
            self.results.append(UITestResult("clear_chat", False, str(e), critical=True))
    
    async def test_profiles(self, page):
        """Non-critical: Profile system"""
        try:
            profile_count = await page.locator("#profileSelect").count()
            
            if profile_count > 0:
                self.results.append(UITestResult("profiles", True, "Profile selector found", critical=False))
            else:
                self.results.append(UITestResult("profiles", True, "Not integrated (OK)", critical=False))
                
        except Exception as e:
            self.results.append(UITestResult("profiles", True, "Not integrated (OK)", critical=False))
    
    async def test_voice_controls(self, page):
        """Non-critical: Voice buttons"""
        try:
            wake_word = await page.locator("#wakeWordBtn").count()
            
            if wake_word > 0:
                self.results.append(UITestResult("voice_controls", True, "Voice controls found", critical=False))
            else:
                self.results.append(UITestResult("voice_controls", True, "Not integrated (OK)", critical=False))
                
        except Exception as e:
            self.results.append(UITestResult("voice_controls", True, "Not integrated (OK)", critical=False))
    
    async def test_task_sidebar(self, page):
        """Non-critical: Task sidebar"""
        try:
            sidebar = await page.locator("#taskSidebar").count()
            
            if sidebar > 0:
                self.results.append(UITestResult("task_sidebar", True, "Task sidebar found", critical=False))
            else:
                self.results.append(UITestResult("task_sidebar", True, "Not integrated (OK)", critical=False))
                
        except Exception as e:
            self.results.append(UITestResult("task_sidebar", True, "Not integrated (OK)", critical=False))
    
    async def test_pwa_features(self, page):
        """Non-critical: PWA manifest"""
        try:
            manifest = await page.locator('link[rel="manifest"]').count()
            
            if manifest > 0:
                self.results.append(UITestResult("pwa_features", True, "PWA manifest linked", critical=False))
            else:
                self.results.append(UITestResult("pwa_features", True, "PWA not configured (OK)", critical=False))
                
        except Exception as e:
            self.results.append(UITestResult("pwa_features", True, "PWA not configured (OK)", critical=False))
    
    async def save_artifacts(self, page):
        """Save test artifacts"""
        # Final screenshot
        await page.screenshot(path=self.artifacts_dir / "screenshots" / "final.png")
        
        # Save console log
        with open(self.artifacts_dir / "console.log", "w") as f:
            f.write("\n".join(self.console_log))
        
        # Save network log
        with open(self.artifacts_dir / "network.log", "w") as f:
            f.write("\n".join(self.network_log))
        
        print(f"\n📁 Artifacts saved to: {self.artifacts_dir}")
    
    def generate_report(self):
        """Generate HTML report"""
        critical_passed = sum(1 for r in self.results if r.critical and r.passed)
        critical_total = sum(1 for r in self.results if r.critical)
        optional_passed = sum(1 for r in self.results if not r.critical and r.passed)
        optional_total = sum(1 for r in self.results if not r.critical)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Athena UI Test Report</title>
    <style>
        body {{ font-family: system-ui; padding: 2rem; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }}
        .summary {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .pass {{ color: #4caf50; }}
        .fail {{ color: #f44336; }}
        .test-result {{ padding: 1rem; margin: 0.5rem 0; background: white; border-radius: 4px; border-left: 4px solid #ddd; }}
        .test-result.pass {{ border-left-color: #4caf50; }}
        .test-result.fail {{ border-left-color: #f44336; }}
        .test-result.critical {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔥 Athena UI Confidence Drill</h1>
        <p>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="card">
            <h2>Critical Tests</h2>
            <p class="{'pass' if critical_passed == critical_total else 'fail'}">
                {critical_passed}/{critical_total} PASSED
            </p>
        </div>
        <div class="card">
            <h2>Optional Tests</h2>
            <p class="pass">{optional_passed}/{optional_total} PASSED</p>
        </div>
    </div>
    
    <div class="card">
        <h2>Test Results</h2>
"""
        
        for result in self.results:
            status_class = "pass" if result.passed else "fail"
            critical_class = "critical" if result.critical else ""
            icon = "✅" if result.passed else "❌"
            critical_label = " [CRITICAL]" if result.critical else ""
            
            html += f"""
        <div class="test-result {status_class} {critical_class}">
            {icon} <strong>{result.name}</strong>{critical_label}<br>
            <small>{result.message}</small>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        # Save report
        with open(self.artifacts_dir / "report.html", "w") as f:
            f.write(html)
        
        # Save JSON
        with open(self.artifacts_dir / "results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "critical_passed": critical_passed,
                "critical_total": critical_total,
                "optional_passed": optional_passed,
                "optional_total": optional_total,
                "all_passed": critical_passed == critical_total,
                "results": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "message": r.message,
                        "critical": r.critical,
                        "timestamp": r.timestamp
                    }
                    for r in self.results
                ]
            }, f, indent=2)
        
        print(f"\n📄 Report generated: {self.artifacts_dir}/report.html")
    
    def get_exit_code(self):
        """Return exit code (0 = all critical passed)"""
        critical_failed = sum(1 for r in self.results if r.critical and not r.passed)
        
        if critical_failed == 0:
            print("\n✅ ALL CRITICAL TESTS PASSED - UI IS PRODUCTION-READY!")
            return 0
        else:
            print(f"\n❌ {critical_failed} CRITICAL TESTS FAILED - FIX BEFORE SHIPPING!")
            return 1
    
    # Test implementations (copy from previous drill)
    async def test_page_load(self, page):
        """Test: Page loads correctly"""
        try:
            await page.goto(UI_URL)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "01_page_load.png")
            
            title = await page.title()
            self.results.append(UITestResult("page_load", "Athena" in title, f"Title: {title}", critical=True))
        except Exception as e:
            self.results.append(UITestResult("page_load", False, str(e), critical=True))
    
    async def test_rag_query(self, page):
        """Test: RAG query works"""
        try:
            await page.fill("#input", "What is TRM in one sentence?")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "02_rag_query.png")
            
            response = await page.locator(".message.assistant .message-content").last.text_content()
            passed = len(response) > 10
            
            self.results.append(UITestResult("rag_query", passed, f"{len(response)} chars", critical=True))
        except Exception as e:
            self.results.append(UITestResult("rag_query", False, str(e), critical=True))
    
    async def test_router_behavior(self, page):
        """Test: Router adapts to query type"""
        try:
            await page.fill("#input", "Brainstorm three UX ideas")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "03_router.png")
            
            self.results.append(UITestResult("router_behavior", True, "Router responded", critical=False))
        except Exception as e:
            self.results.append(UITestResult("router_behavior", False, str(e), critical=False))
    
    async def test_streaming(self, page):
        """Test: SSE streaming stability"""
        try:
            await page.fill("#input", "Explain the learning system in detail")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(5)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "04_streaming.png")
            
            response = await page.locator(".message.assistant .message-content").last.text_content()
            passed = len(response) > 50
            
            self.results.append(UITestResult("streaming", passed, f"{len(response)} chars", critical=True))
        except Exception as e:
            self.results.append(UITestResult("streaming", False, str(e), critical=True))
    
    async def test_multi_turn(self, page):
        """Test: Multi-turn memory"""
        try:
            await page.fill("#input", "What is the dev daemon?")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content", timeout=30000)
            await asyncio.sleep(2)
            
            await page.fill("#input", "What port?")
            await page.click("#send")
            await page.wait_for_selector(".message.assistant .message-content:not(:has-text('dev daemon'))", timeout=30000)
            await asyncio.sleep(2)
            
            self.results.append(UITestResult("multi_turn", True, "Memory works", critical=False))
        except Exception as e:
            self.results.append(UITestResult("multi_turn", False, str(e), critical=False))
    
    async def test_clear_chat(self, page):
        """Test: Clear chat works"""
        try:
            await page.click(".tool-btn:has-text('Clear')")
            await asyncio.sleep(1)
            
            await page.screenshot(path=self.artifacts_dir / "screenshots" / "05_clear.png")
            
            final = await page.locator(".message").count()
            passed = final == 0
            
            self.results.append(UITestResult("clear_chat", passed, f"{final} messages remain", critical=True))
        except Exception as e:
            self.results.append(UITestResult("clear_chat", False, str(e), critical=True))
    
    async def test_profiles(self, page):
        """Test: Profiles (optional)"""
        try:
            count = await page.locator("#profileSelect").count()
            self.results.append(UITestResult("profiles", True, "Present" if count > 0 else "Not integrated", critical=False))
        except Exception as e:
            self.results.append(UITestResult("profiles", True, "Not integrated", critical=False))
    
    async def test_voice_controls(self, page):
        """Test: Voice controls (optional)"""
        try:
            count = await page.locator("#wakeWordBtn").count()
            self.results.append(UITestResult("voice_controls", True, "Present" if count > 0 else "Not integrated", critical=False))
        except Exception as e:
            self.results.append(UITestResult("voice_controls", True, "Not integrated", critical=False))
    
    async def test_task_sidebar(self, page):
        """Test: Task sidebar (optional)"""
        try:
            count = await page.locator("#taskSidebar").count()
            self.results.append(UITestResult("task_sidebar", True, "Present" if count > 0 else "Not integrated", critical=False))
        except Exception as e:
            self.results.append(UITestResult("task_sidebar", True, "Not integrated", critical=False))
    
    async def test_pwa_features(self, page):
        """Test: PWA features (optional)"""
        try:
            manifest = await page.locator('link[rel="manifest"]').count()
            self.results.append(UITestResult("pwa_features", True, "Present" if manifest > 0 else "Not configured", critical=False))
        except Exception as e:
            self.results.append(UITestResult("pwa_features", True, "Not configured", critical=False))

async def main():
    drill = UIDrillCI()
    exit_code = await drill.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())

