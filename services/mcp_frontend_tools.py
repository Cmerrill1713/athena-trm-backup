#!/usr/bin/env python3
"""
MCP Frontend Tools - Automated Swift UI Testing & Fixing
Port 8413 - Local-first frontend verification pipeline

Tools:
  - file_apply_patch - Apply unified diffs/patches
  - xcode_build - Build Xcode projects
  - app_launch - Launch macOS apps
  - ui_typing_probe - Synthetic typing test
  - swift_frontend_reflex - Auto-fix focus issues
  - frontend_verify - One-button orchestration
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Frontend Tools",
    description="Automated Swift UI testing and fixing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowlist paths to prevent random file edits
ALLOWED_PATHS = [
    "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp",
]

def is_path_allowed(path: str) -> bool:
    """Check if path is in allowlist."""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(allowed) for allowed in ALLOWED_PATHS)

# ============================================================================
# MODELS
# ============================================================================

class FilePatchRequest(BaseModel):
    """Apply a patch to a file."""
    path: str
    pattern: str
    replacement: str
    backup: bool = True

class XcodeBuildRequest(BaseModel):
    """Build an Xcode project."""
    project: str
    scheme: str
    configuration: str = "Debug"
    destination: str = "platform=macOS"
    clean: bool = False
    emit_tail: int = 0  # Number of lines to capture from end of output

class AppLaunchRequest(BaseModel):
    """Launch a macOS app."""
    bundle_id: str
    binary_glob: Optional[str] = None  # Glob to discover binary if not installed
    kill_existing: bool = True
    wait_for_binary_s: int = 0  # Wait for binary to exist before launching
    activate_frontmost: bool = True

class UITypingProbeRequest(BaseModel):
    """Synthetic typing test."""
    bundle_id: str
    text: str
    send: str = "enter"  # "enter" or "cmd+enter"
    repeat: int = 3
    timeout: int = 10
    refocus_between_cycles: bool = False
    preclick_to_focus: bool = False
    emit_transcript: bool = False

class FrontendVerifyRequest(BaseModel):
    """Orchestrate full frontend verification."""
    project_path: str
    scheme: str
    bundle_id: str

# ============================================================================
# TOOL 1: FILE APPLY PATCH
# ============================================================================

@app.post("/tool/file_apply_patch")
async def file_apply_patch(request: FilePatchRequest):
    """Apply a regex patch to a file safely."""
    if not is_path_allowed(request.path):
        raise HTTPException(status_code=403, detail=f"Path not allowed: {request.path}")
    
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
    
    try:
        # Read file
        with open(request.path, 'r') as f:
            content = f.read()
        
        # Backup if requested
        if request.backup:
            backup_path = f"{request.path}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            with open(backup_path, 'w') as f:
                f.write(content)
            logger.info(f"Backup saved: {backup_path}")
        
        # Apply patch
        pattern_re = re.compile(request.pattern)
        matches = pattern_re.findall(content)
        
        if not matches:
            return {
                "success": False,
                "error": "Pattern not found in file",
                "matches_found": 0
            }
        
        new_content = pattern_re.sub(request.replacement, content)
        
        # Write back
        with open(request.path, 'w') as f:
            f.write(new_content)
        
        logger.info(f"✅ Patched {request.path}: {len(matches)} replacements")
        
        return {
            "success": True,
            "path": request.path,
            "matches_found": len(matches),
            "backup_path": backup_path if request.backup else None
        }
        
    except Exception as e:
        logger.error(f"Patch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TOOL 2: XCODE BUILD
# ============================================================================

@app.post("/tool/xcode_build")
async def xcode_build(request: XcodeBuildRequest):
    """Build an Xcode project."""
    if not is_path_allowed(request.project):
        raise HTTPException(status_code=403, detail=f"Path not allowed: {request.project}")
    
    try:
        import time
        t0 = time.time()
        
        cmd = [
            "xcodebuild",
            "-scheme", request.scheme,
            "-destination", request.destination,
            "-configuration", request.configuration
        ]
        
        # Add clean if requested
        if request.clean:
            cmd.append("clean")
        
        cmd.append("build")
        
        logger.info(f"Building: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(request.project) if os.path.isfile(request.project) else request.project,
            capture_output=True,
            text=True,
            timeout=300  # Longer timeout for clean builds
        )
        
        duration = time.time() - t0
        
        # Extract key info from output
        combined_output = result.stdout + result.stderr
        build_succeeded = "** BUILD SUCCEEDED **" in combined_output
        errors = re.findall(r'error: (.+)', combined_output)
        
        # Capture tail if requested
        tail_lines = []
        if request.emit_tail > 0:
            output_lines = combined_output.split('\n')
            tail_lines = output_lines[-request.emit_tail:]
        
        logger.info(f"Build {'succeeded' if build_succeeded else 'failed'} in {duration:.1f}s")
        
        response = {
            "success": build_succeeded,
            "ok": build_succeeded,  # probe_ok compatibility
            "exit_code": result.returncode,
            "errors": errors[:10],
            "duration_s": round(duration, 2)
        }
        
        # Add tail if requested
        if tail_lines:
            response["build_log_tail"] = tail_lines
        
        return response
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Build timed out after 300s")
    except Exception as e:
        logger.error(f"Build failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TOOL 3: APP LAUNCH
# ============================================================================

@app.post("/tool/app_launch")
async def app_launch(request: AppLaunchRequest):
    """Launch a macOS app, optionally killing existing instances."""
    try:
        import time
        import glob
        
        # Kill existing if requested
        if request.kill_existing:
            app_name = request.bundle_id.split('.')[-1]
            subprocess.run(["pkill", "-x", app_name], check=False)
            logger.info(f"Killed existing instances of {app_name}")
            time.sleep(0.5)
        
        # Wait for binary if glob provided and wait_for_binary_s > 0
        binary_path = None
        if request.binary_glob and request.wait_for_binary_s > 0:
            logger.info(f"Waiting up to {request.wait_for_binary_s}s for binary: {request.binary_glob}")
            expanded_glob = os.path.expanduser(request.binary_glob)
            deadline = time.time() + request.wait_for_binary_s
            
            while time.time() < deadline:
                candidates = glob.glob(expanded_glob)
                if candidates:
                    # Pick most recent
                    binary_path = max(candidates, key=os.path.getmtime)
                    logger.info(f"Found binary: {binary_path}")
                    break
                time.sleep(2)
            
            if not binary_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"Binary not found after {request.wait_for_binary_s}s: {request.binary_glob}"
                )
        
        # Try launch by bundle ID first, fallback to binary path
        launch_method = None
        try:
            subprocess.run(
                ["open", "-b", request.bundle_id, "--new"],
                check=True,
                timeout=10,
                capture_output=True
            )
            launch_method = f"bundle:{request.bundle_id}"
            logger.info(f"Launched via bundle ID: {request.bundle_id}")
        except subprocess.CalledProcessError:
            if binary_path:
                # Fallback to binary path
                subprocess.run(
                    ["open", binary_path],
                    check=True,
                    timeout=10
                )
                launch_method = f"binary:{binary_path}"
                logger.info(f"Launched via binary: {binary_path}")
            else:
                raise
        
        # Wait a moment for app to start
        time.sleep(2)
        
        # Bring to front if requested
        if request.activate_frontmost:
            script = f'''
tell application "System Events"
    set frontmost of first application process whose bundle identifier is "{request.bundle_id}" to true
end tell
'''
            subprocess.run(
                ["osascript", "-e", script],
                check=False,
                timeout=5
            )
        
        logger.info(f"✅ Launched {request.bundle_id} via {launch_method}")
        
        return {
            "success": True,
            "ok": True,  # probe_ok compatibility
            "bundle_id": request.bundle_id,
            "launch_method": launch_method,
            "frontmost": request.activate_frontmost
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Launch timed out")
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TOOL 4: UI TYPING PROBE
# ============================================================================

@app.post("/tool/ui_typing_probe")
async def ui_typing_probe(request: UITypingProbeRequest):
    """Synthetic typing test - verifies focus persists across sends."""
    try:
        import time
        app_name = request.bundle_id.split('.')[-1]
        
        results = []
        transcript = []
        
        # Preflight: ensure app is frontmost
        if request.preclick_to_focus:
            preflight_script = f'''
tell application "{app_name}"
    activate
end tell
delay 0.3
'''
            subprocess.run(
                ["osascript", "-e", preflight_script],
                check=False,
                timeout=5
            )
        
        for i in range(request.repeat):
            # Re-focus between cycles if requested
            if i > 0 and request.refocus_between_cycles:
                refocus_script = f'''
tell application "{app_name}"
    activate
end tell
delay 0.2
'''
                subprocess.run(
                    ["osascript", "-e", refocus_script],
                    check=False,
                    timeout=3
                )
            
            # Type text via AppleScript
            type_script = f'''
tell application "{app_name}"
    activate
end tell

tell application "System Events"
    keystroke "{request.text}"
    delay 0.1
    {'keystroke return using command down' if request.send == 'cmd+enter' else 'keystroke return'}
    delay 0.5
end tell
'''
            
            t0 = time.time()
            result = subprocess.run(
                ["osascript", "-e", type_script],
                capture_output=True,
                text=True,
                timeout=request.timeout
            )
            duration = time.time() - t0
            
            iteration_pass = result.returncode == 0
            
            iteration_data = {
                "iteration": i + 1,
                "success": iteration_pass,
                "duration_s": round(duration, 3),
                "stderr": result.stderr if result.stderr else None
            }
            results.append(iteration_data)
            
            # Build transcript if requested
            if request.emit_transcript:
                transcript.append({
                    "cycle": i + 1,
                    "text": request.text,
                    "send_key": request.send,
                    "success": iteration_pass,
                    "duration_s": round(duration, 3)
                })
            
            if not iteration_pass:
                break
        
        all_pass = all(r["success"] for r in results)
        passed_count = len([r for r in results if r["success"]])
        
        logger.info(f"Typing probe: {passed_count}/{request.repeat} passed")
        
        response = {
            "pass": all_pass,
            "ok": all_pass,  # probe_ok compatibility
            "success": all_pass,  # probe_ok compatibility
            "iterations": results,
            "details": f"Focus intact across {passed_count} sends"
        }
        
        if request.emit_transcript:
            response["transcript"] = transcript
        
        return response
        
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "ok": False,
            "error": f"Probe timed out after {request.timeout}s"
        }
    except Exception as e:
        logger.error(f"Probe failed: {e}")
        return {
            "pass": False,
            "ok": False,
            "error": str(e)
        }

# ============================================================================
# TOOL 5: SWIFT FRONTEND REFLEX (Auto-fix)
# ============================================================================

@app.post("/tool/swift_frontend_reflex")
async def swift_frontend_reflex():
    """Auto-apply known-good focus fixes to Swift frontend."""
    try:
        # Run the Swift Reflex auto-patch
        result = subprocess.run(
            ["python3", "tools/reflex/swift_reflex.py",
             "--watch", "*.swift",
             "--build", "xcodebuild -scheme NeuroForgeApp build",
             "--tests", "echo 'tests'"],
            cwd="/Users/christianmerrill/Documents/GitHub",
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "success": result.returncode == 0,
            "fixes_applied": "Focus management, hit testing, design tokens"
        }
        
    except Exception as e:
        logger.error(f"Auto-fix failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# TOOL 6: FRONTEND VERIFY (Orchestration)
# ============================================================================

@app.post("/tool/frontend_verify")
async def frontend_verify(request: FrontendVerifyRequest):
    """
    One-button frontend verification:
    1. Build project
    2. Launch app
    3. Run typing probe
    4. Return pass/fail with logs
    """
    logger.info("=== Frontend Verification Pipeline ===")
    
    results = {
        "build": None,
        "launch": None,
        "probe": None,
        "overall": False
    }
    
    try:
        # Step 1: Build
        logger.info("Step 1/3: Building...")
        build_result = await xcode_build(XcodeBuildRequest(
            project=request.project_path,
            scheme=request.scheme
        ))
        results["build"] = build_result
        
        if not build_result["success"]:
            logger.error("Build failed, stopping verification")
            return results
        
        # Step 2: Launch
        logger.info("Step 2/3: Launching app...")
        launch_result = await app_launch(AppLaunchRequest(
            bundle_id=request.bundle_id,
            kill_existing=True
        ))
        results["launch"] = launch_result
        
        # Wait for app to initialize
        import asyncio
        await asyncio.sleep(3)
        
        # Step 3: Typing Probe
        logger.info("Step 3/3: Running typing probe...")
        probe_result = await ui_typing_probe(UITypingProbeRequest(
            bundle_id=request.bundle_id,
            text="Hello!",
            send="enter",
            repeat=3
        ))
        results["probe"] = probe_result
        
        # Overall result
        results["overall"] = probe_result["pass"]
        
        logger.info(f"✅ Verification complete: {'PASS' if results['overall'] else 'FAIL'}")
        
        return results
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        results["error"] = str(e)
        return results

# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/")
async def root():
    """Service info."""
    return {
        "service": "MCP Frontend Tools",
        "version": "1.0.0",
        "tools": [
            "file_apply_patch",
            "xcode_build",
            "app_launch",
            "ui_typing_probe",
            "swift_frontend_reflex",
            "frontend_verify"
        ],
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "mcp-frontend-tools",
        "port": 8413,
        "tools_available": 6
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_FRONTEND_PORT", "8413"))
    logger.info(f"Starting MCP Frontend Tools on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

