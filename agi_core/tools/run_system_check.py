"""
System Check Tool - Forces AI to use DAG-based health check
"""
import subprocess, json, shlex
from pathlib import Path

NAME = "run_system_check"
DESC = "Runs the full DAG-based system health check and returns a JSON report with all service statuses, gates, and metrics."

def run_system_check() -> dict:
    """
    Execute the full system health check DAG.
    Returns a structured JSON report with pass/fail gates.
    """
    try:
        # Get the project root
        root = Path(__file__).parent.parent.parent
        script = root / "scripts" / "system_check_dag.py"
        
        if not script.exists():
            return {
                "status": "ERROR",
                "error": f"System check script not found at {script}"
            }
        
        # Run the DAG
        p = subprocess.run(
            ["python3", str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(root)
        )
        
        # Try to parse JSON output
        try:
            # Look for JSON in stdout
            lines = p.stdout.strip().split('\n')
            for line in reversed(lines):  # Check from end
                if line.strip().startswith('{'):
                    data = json.loads(line)
                    return data
            
            # If no JSON found, check the artifacts file
            report_file = root / "artifacts" / "system_check_dag_report.json"
            if report_file.exists():
                with open(report_file) as f:
                    return json.load(f)
            
            # Fallback: return raw output
            return {
                "status": "PASS" if p.returncode == 0 else "FAIL",
                "stdout": p.stdout[-1000:],
                "stderr": p.stderr[-1000:],
                "returncode": p.returncode
            }
            
        except json.JSONDecodeError:
            return {
                "status": "ERROR",
                "error": "Could not parse JSON output",
                "stdout": p.stdout[-1000:],
                "stderr": p.stderr[-1000:]
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "ERROR",
            "error": "System check timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }

# Tool schema for agent registry
TOOL_SCHEMA = {
    "name": "run_system_check",
    "description": "Execute full DAG-based system health check with parallel verification and hard gates. Returns JSON report with service statuses, failures, warnings, and metrics.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

if __name__ == "__main__":
    # Test the tool
    result = run_system_check()
    print(json.dumps(result, indent=2))


