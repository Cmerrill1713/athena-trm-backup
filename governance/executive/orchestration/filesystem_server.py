"""
Filesystem MCP Server
Provides safe file operations for LLM agents
"""
import os
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("filesystem", dependencies=["pathlib"])

# Safe directory - restrict operations to this path
SAFE_DIR = os.getenv("MCP_FILESYSTEM_ROOT", "/tmp/mcp_files")
os.makedirs(SAFE_DIR, exist_ok=True)

def _safe_path(path: str) -> Path:
    """Ensure path is within safe directory"""
    safe = Path(SAFE_DIR).resolve()
    target = (safe / path).resolve()
    if not str(target).startswith(str(safe)):
        raise ValueError(f"Path {path} is outside safe directory")
    return target

@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> dict:
    """
    Read contents of a file
    
    Args:
        path: Relative path within safe directory
        encoding: File encoding (default: utf-8)
    
    Returns:
        File contents and metadata
    """
    try:
        file_path = _safe_path(path)

        if not file_path.exists():
            return {"error": f"File not found: {path}", "status": "failed"}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}", "status": "failed"}

        content = file_path.read_text(encoding=encoding)

        return {
            "content": content,
            "path": path,
            "size": file_path.stat().st_size,
            "lines": len(content.splitlines()),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def write_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """
    Write content to a file
    
    Args:
        path: Relative path within safe directory
        content: Content to write
        encoding: File encoding (default: utf-8)
    
    Returns:
        Write operation result
    """
    try:
        file_path = _safe_path(path)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding=encoding)

        return {
            "path": path,
            "size": file_path.stat().st_size,
            "lines": len(content.splitlines()),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def list_files(path: str = "", pattern: str = "*") -> dict:
    """
    List files and directories
    
    Args:
        path: Relative path within safe directory (default: root)
        pattern: Glob pattern (default: *)
    
    Returns:
        List of files and directories
    """
    try:
        dir_path = _safe_path(path)

        if not dir_path.exists():
            return {"error": f"Directory not found: {path}", "status": "failed"}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}", "status": "failed"}

        items = []
        for item in sorted(dir_path.glob(pattern)):
            relative = item.relative_to(Path(SAFE_DIR))
            items.append({
                "name": item.name,
                "path": str(relative),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })

        return {
            "path": path,
            "items": items,
            "count": len(items),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def delete_file(path: str) -> dict:
    """
    Delete a file
    
    Args:
        path: Relative path within safe directory
    
    Returns:
        Delete operation result
    """
    try:
        file_path = _safe_path(path)

        if not file_path.exists():
            return {"error": f"File not found: {path}", "status": "failed"}

        if file_path.is_dir():
            return {"error": f"Cannot delete directory: {path}", "status": "failed"}

        file_path.unlink()

        return {
            "path": path,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def create_directory(path: str) -> dict:
    """
    Create a directory
    
    Args:
        path: Relative path within safe directory
    
    Returns:
        Create operation result
    """
    try:
        dir_path = _safe_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)

        return {
            "path": path,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

