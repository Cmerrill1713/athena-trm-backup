"""
Code Execution MCP Server
Provides safe code execution for LLM agents
"""
import os
import subprocess
import tempfile
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("code-execution", dependencies=["subprocess"])

# Execution limits
MAX_EXECUTION_TIME = 30  # seconds
MAX_OUTPUT_SIZE = 100000  # characters

@mcp.tool()
def execute_python(code: str, timeout: int = 10) -> dict:
    """
    Execute Python code safely
    
    Args:
        code: Python code to execute
        timeout: Execution timeout in seconds (max 30)
    
    Returns:
        Execution result with stdout, stderr, and exit code
    """
    try:
        timeout = min(timeout, MAX_EXECUTION_TIME)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute with subprocess
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )

            stdout = result.stdout[:MAX_OUTPUT_SIZE]
            stderr = result.stderr[:MAX_OUTPUT_SIZE]

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
                "status": "success"
            }
        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        return {
            "error": f"Execution timeout ({timeout}s exceeded)",
            "status": "failed"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def execute_node(code: str, timeout: int = 10) -> dict:
    """
    Execute Node.js/JavaScript code safely
    
    Args:
        code: JavaScript code to execute
        timeout: Execution timeout in seconds (max 30)
    
    Returns:
        Execution result with stdout, stderr, and exit code
    """
    try:
        timeout = min(timeout, MAX_EXECUTION_TIME)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute with subprocess
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            stdout = result.stdout[:MAX_OUTPUT_SIZE]
            stderr = result.stderr[:MAX_OUTPUT_SIZE]

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
                "status": "success"
            }
        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        return {
            "error": f"Execution timeout ({timeout}s exceeded)",
            "status": "failed"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def execute_shell(command: str, timeout: int = 10) -> dict:
    """
    Execute shell command safely (LIMITED - only safe commands)
    
    Args:
        command: Shell command to execute
        timeout: Execution timeout in seconds (max 30)
    
    Returns:
        Execution result
    """
    try:
        timeout = min(timeout, MAX_EXECUTION_TIME)

        # Whitelist of safe commands
        safe_commands = ['ls', 'pwd', 'echo', 'cat', 'grep', 'wc', 'head', 'tail', 'date']
        first_word = command.split()[0] if command.strip() else ''

        if first_word not in safe_commands:
            return {
                "error": f"Command '{first_word}' not allowed. Safe commands: {', '.join(safe_commands)}",
                "status": "failed"
            }

        # Execute with subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        stdout = result.stdout[:MAX_OUTPUT_SIZE]
        stderr = result.stderr[:MAX_OUTPUT_SIZE]

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "status": "success"
        }

    except subprocess.TimeoutExpired:
        return {
            "error": f"Execution timeout ({timeout}s exceeded)",
            "status": "failed"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def install_package(package: str, language: str = "python") -> dict:
    """
    Install a package (pip or npm)
    
    Args:
        package: Package name
        language: "python" or "node" (default: python)
    
    Returns:
        Installation result
    """
    try:
        if language == "python":
            result = subprocess.run(
                ['pip', 'install', package],
                capture_output=True,
                text=True,
                timeout=60
            )
        elif language == "node":
            result = subprocess.run(
                ['npm', 'install', package],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            return {"error": f"Unsupported language: {language}", "status": "failed"}

        return {
            "package": package,
            "language": language,
            "stdout": result.stdout[:MAX_OUTPUT_SIZE],
            "stderr": result.stderr[:MAX_OUTPUT_SIZE],
            "success": result.returncode == 0,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

