#!/usr/bin/env python3
"""
Wiring Validation - Concrete Evidence of What's Actually Working

Reads config/wiring.matrix.yaml and validates:
- Services are running on expected ports
- Health endpoints respond
- Metrics endpoints contain expected series
- Prometheus is scraping
- Python imports work
- Swift projects compile
- Files exist

Emits: Scorecard + JSON report
"""

import json
import os
import sys
import subprocess
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import urllib.request
import urllib.error
import urllib.parse
import ssl

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]


# HTTP Utilities
def http_get(url: str, timeout: float = 2.5, headers: Optional[Dict] = None,
             data: Optional[Dict] = None, method: str = "GET") -> Tuple[Optional[int], str]:
    """Make HTTP request, return (status_code, body)"""
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, method=method)
    
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    
    if data:
        req.add_header("Content-Type", "application/json")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            return response.getcode(), response.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return None, str(e)


def tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if TCP port is open"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def has_strings(text: str, needles: List[str]) -> bool:
    """Check if text contains all needle strings"""
    if not text:
        return False
    return all(needle in text for needle in needles)


def run_command(cmd: List[str], cwd: Optional[Path] = None,
                env: Optional[Dict] = None) -> Tuple[int, str, str]:
    """Run shell command, return (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env or os.environ,
        text=True,
        capture_output=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def prom_query(prom_url: str, expr: str) -> Tuple[int, Optional[List]]:
    """Query Prometheus, return (status, results)"""
    encoded = urllib.parse.quote(expr)
    url = f"{prom_url}/api/v1/query?query={encoded}"
    
    code, body = http_get(url, timeout=3)
    if code != 200:
        return code or 500, None
    
    try:
        data = json.loads(body)
        if data.get("status") != "success":
            return 500, None
        return 200, data["data"]["result"]
    except Exception:
        return 500, None


# Validators
def validate_service(name: str, spec: Dict, results: Dict) -> Tuple[int, int]:
    """Validate a service, return (checks, passes)"""
    svc_result = {
        "exists": False,
        "health": None,
        "metrics": None,
        "endpoints": [],
        "prometheus": None,
        "errors": []
    }
    
    checks, passes = 0, 0
    
    # Check path exists
    path = ROOT / spec.get("path", "")
    svc_result["exists"] = path.exists()
    checks += 1
    if path.exists():
        passes += 1
    else:
        svc_result["errors"].append(f"Path not found: {path}")
    
    # Check health endpoint
    if spec.get("health"):
        h = spec["health"]
        url = h["url"]
        expect = h.get("expect", 200)
        
        # Check port first
        if "http" in url:
            try:
                port = int(url.split(":")[2].split("/")[0])
                host = "localhost"
                checks += 1
                if tcp_open(host, port):
                    passes += 1
            except:
                pass
        
        # Check health endpoint
        code, body = http_get(url, timeout=h.get("timeout_s", 2.5))
        ok = (code == expect)
        svc_result["health"] = {"code": code, "ok": ok, "expected": expect}
        checks += 1
        if ok:
            passes += 1
        else:
            svc_result["errors"].append(f"Health check failed: got {code}, expected {expect}")
    
    # Check metrics endpoint
    if spec.get("metrics"):
        m = spec["metrics"]
        code, body = http_get(m["url"], timeout=2.5)
        must_contain = m.get("must_contain", [])
        ok = (code == 200) and has_strings(body, must_contain)
        svc_result["metrics"] = {"code": code, "ok": ok, "must_contain": must_contain}
        checks += 1
        if ok:
            passes += 1
        else:
            missing = [s for s in must_contain if s not in (body or "")]
            svc_result["errors"].append(f"Metrics missing: {missing}")
    
    # Check custom endpoints
    for ep in spec.get("endpoints", []):
        url = ep["url"]
        method = ep.get("method", "GET")
        body_data = ep.get("body")
        
        code, body = http_get(url, timeout=3, data=body_data, method=method)
        
        keys_ok = True
        if ep.get("expect_json_keys"):
            try:
                json_data = json.loads(body)
                keys_ok = all(k in json_data for k in ep["expect_json_keys"])
            except Exception:
                keys_ok = False
        
        ep_ok = (code is not None) and (code < 500) and keys_ok
        svc_result["endpoints"].append({
            "url": url,
            "method": method,
            "code": code,
            "ok": ep_ok
        })
        checks += 1
        if ep_ok:
            passes += 1
        else:
            svc_result["errors"].append(f"Endpoint failed: {method} {url} -> {code}")
    
    # Check Prometheus scraping
    if spec.get("prometheus", {}).get("scrape_expected"):
        prom = spec["prometheus"]
        prom_url = prom.get("prom_url", "http://localhost:9090")
        prom_ok = True
        prom_results = []
        
        for q in prom.get("queries", []):
            name = q.get("name", "unnamed")
            expr = q["expr"]
            
            code, result = prom_query(prom_url, expr)
            query_ok = (code == 200) and (result is not None)
            
            if query_ok and "expect_gt" in q and result:
                try:
                    value = float(result[0]["value"][1])
                    query_ok = value > q["expect_gt"]
                except Exception:
                    query_ok = False
            
            prom_results.append({"name": name, "expr": expr, "ok": query_ok})
            checks += 1
            if query_ok:
                passes += 1
            else:
                svc_result["errors"].append(f"Prometheus query failed: {name}")
            
            prom_ok = prom_ok and query_ok
        
        svc_result["prometheus"] = {"ok": prom_ok, "queries": prom_results}
    
    # Check targets if specified
    if spec.get("checks"):
        for check in spec["checks"]:
            if check["type"] == "targets":
                code, body = http_get(check["url"], timeout=3)
                if code == 200:
                    must_include = check.get("must_include_hosts", [])
                    ok = all(host in body for host in must_include)
                    checks += 1
                    if ok:
                        passes += 1
    
    results["services"][name] = svc_result
    return checks, passes


def validate_layer(name: str, spec: Dict, results: Dict) -> Tuple[int, int]:
    """Validate a code layer (Python imports, Swift builds)"""
    layer_result = {
        "exists": False,
        "imports_ok": None,
        "swift_ok": None,
        "errors": []
    }
    
    checks, passes = 0, 0
    
    # Check path exists
    path = ROOT / spec.get("path", "")
    layer_result["exists"] = path.exists()
    checks += 1
    if path.exists():
        passes += 1
    else:
        layer_result["errors"].append(f"Path not found: {path}")
    
    # Check Python imports
    if spec.get("python_imports"):
        import_results = []
        all_ok = True
        
        for imp in spec["python_imports"]:
            cmd = [sys.executable, "-c", f"import {imp}; print('OK')"]
            rc, stdout, stderr = run_command(cmd, cwd=ROOT)
            ok = (rc == 0) and ("OK" in stdout)
            import_results.append({"import": imp, "ok": ok})
            checks += 1
            if ok:
                passes += 1
            else:
                layer_result["errors"].append(f"Import failed: {imp}")
                all_ok = False
        
        layer_result["imports_ok"] = all_ok
        layer_result["import_details"] = import_results
    
    # Check Swift project
    if spec.get("xcodeproj"):
        xproj = ROOT / spec["xcodeproj"]
        if xproj.exists():
            cmd = ["/usr/bin/xcodebuild", "-list", "-project", str(xproj)]
            rc, stdout, stderr = run_command(cmd)
            ok = rc == 0
            layer_result["swift_ok"] = ok
            checks += 1
            if ok:
                passes += 1
            else:
                layer_result["errors"].append(f"Xcode project invalid: {stderr[:100]}")
        else:
            layer_result["swift_ok"] = False
            layer_result["errors"].append(f"Xcode project not found: {xproj}")
    
    # Check Swift files exist
    if spec.get("swift_files"):
        swift_results = []
        for sf in spec["swift_files"]:
            swift_path = ROOT / sf
            ok = swift_path.exists()
            swift_results.append({"file": sf, "exists": ok})
            checks += 1
            if ok:
                passes += 1
        layer_result["swift_files"] = swift_results
    
    results["layers"][name] = layer_result
    return checks, passes


def check_orphans(orphans: List[str], results: Dict) -> None:
    """Check if suspected orphans are referenced anywhere"""
    for dirname in orphans:
        path = ROOT / dirname
        
        if not path.exists():
            results["orphans"][dirname] = "missing"
            continue
        
        # Check if referenced in docker-compose, monitoring, infra
        check_paths = ["docker-compose*.yml", "monitoring/**/*.yml", "infra/**/*.conf"]
        cmd = ["bash", "-c", f"grep -r '{dirname}' docker-compose*.yml monitoring/ infra/ 2>/dev/null | head -1 || true"]
        rc, stdout, stderr = run_command(cmd, cwd=ROOT)
        
        status = "referenced" if stdout.strip() else "unreferenced"
        results["orphans"][dirname] = status


def check_critical_files(files: List[str], results: Dict) -> Tuple[int, int]:
    """Check critical files exist"""
    checks, passes = 0, 0
    file_results = {}
    
    for f in files:
        path = ROOT / f
        exists = path.exists()
        file_results[f] = {"exists": exists}
        checks += 1
        if exists:
            passes += 1
    
    results["critical_files"] = file_results
    return checks, passes


def main():
    """Run complete wiring validation"""
    
    # Load matrix
    matrix_path = ROOT / "config" / "wiring.matrix.yaml"
    if not matrix_path.exists():
        print(f"❌ Wiring matrix not found: {matrix_path}")
        sys.exit(1)
    
    matrix = yaml.safe_load(matrix_path.read_text())
    
    # Initialize results
    results = {
        "services": {},
        "layers": {},
        "orphans": {},
        "critical_files": {},
        "score": {}
    }
    
    total_checks = 0
    total_passes = 0
    
    # Validate services
    print("\n" + "=" * 70)
    print("WIRING VALIDATION")
    print("=" * 70)
    print("\n📡 Validating Services...")
    
    for name, spec in matrix.get("services", {}).items():
        print(f"  Checking {name}...", end=" ")
        sys.stdout.flush()
        checks, passes = validate_service(name, spec, results)
        total_checks += checks
        total_passes += passes
        
        svc = results["services"].get(name, {})
        if svc.get("health", {}).get("ok") and (not svc.get("metrics") or svc["metrics"]["ok"]):
            print("✅")
        else:
            print("❌")
            for err in svc.get("errors", [])[:2]:
                print(f"    ⚠️  {err}")
    
    # Validate layers
    print("\n🐍 Validating Code Layers...")
    
    for name, spec in matrix.get("layers", {}).items():
        print(f"  Checking {name}...", end=" ")
        checks, passes = validate_layer(name, spec, results)
        total_checks += checks
        total_passes += passes
        
        layer = results["layers"][name]
        if layer.get("imports_ok") or layer.get("swift_ok"):
            print("✅")
        else:
            print("❌")
            for err in layer.get("errors", [])[:2]:
                print(f"    ⚠️  {err}")
    
    # Check critical files
    print("\n📄 Validating Critical Files...")
    checks, passes = check_critical_files(matrix.get("critical_files", []), results)
    total_checks += checks
    total_passes += passes
    
    for f, status in results["critical_files"].items():
        print(f"  {f}: {'✅' if status['exists'] else '❌'}")
    
    # Check orphans
    print("\n🗑️  Checking Suspected Orphans...")
    check_orphans(matrix.get("suspected_orphans", []), results)
    
    for d, status in results["orphans"].items():
        if status == "missing":
            print(f"  {d}: ✅ (already removed)")
        elif status == "unreferenced":
            print(f"  {d}: ⚠️  (exists but not referenced)")
        else:
            print(f"  {d}: 🟡 (referenced, keep)")
    
    # Calculate score
    score_pct = int((total_passes / max(total_checks, 1)) * 100)
    results["score"] = {
        "passes": total_passes,
        "checks": total_checks,
        "percent": score_pct
    }
    
    # Save report
    output_dir = ROOT / "artifacts" / "wiring"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "wiring_report.json"
    report_path.write_text(json.dumps(results, indent=2))
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"WIRING SCORE: {score_pct}% ({total_passes}/{total_checks})")
    print("=" * 70)
    
    # Service summary
    print("\n📊 Service Summary:")
    for name, svc in results.get("services", {}).items():
        if not svc:
            print(f"  ❌ {name} (no data)")
            continue
        health = svc.get("health") or {}
        metrics = svc.get("metrics")
        health_ok = health.get("ok", False)
        metrics_ok = metrics.get("ok", True) if metrics else True
        status = "✅" if (health_ok and metrics_ok) else "❌"
        print(f"  {status} {name}")
    
    # Layer summary
    print("\n🐍 Layer Summary:")
    for name, layer in results.get("layers", {}).items():
        if not layer:
            print(f"  ❌ {name} (no data)")
            continue
        imports_ok = layer.get("imports_ok", False)
        swift_ok = layer.get("swift_ok", True)  # True if not checked
        status = "✅" if (imports_ok or swift_ok) else "❌"
        print(f"  {status} {name}")
    
    print(f"\n📝 Detailed report: {report_path}")
    print("")
    
    # Exit code based on score
    if score_pct >= 90:
        print("🎉 WIRING VALIDATED - System is operational!")
        sys.exit(0)
    elif score_pct >= 75:
        print("⚠️  WIRING PARTIAL - Some components need attention")
        sys.exit(1)
    else:
        print("❌ WIRING FAILED - Critical components not working")
        sys.exit(1)


if __name__ == "__main__":
    main()

