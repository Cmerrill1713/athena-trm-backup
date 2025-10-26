"""
Code Access Tool for AGI Agents
Allows agents to read, analyze, and modify their own codebase
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CodeAccessTool:
    """Tool for reading, analyzing, and modifying code"""
    
    def __init__(self, base_path: str = "/Users/christianmerrill/Documents/GitHub"):
        self.base_path = Path(base_path)
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a file from the codebase"""
        try:
            full_path = self.base_path / file_path
            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            content = full_path.read_text()
            return {
                "file_path": file_path,
                "content": content,
                "size": len(content),
                "lines": len(content.split('\n'))
            }
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
    
    def list_files(self, directory: str = "", pattern: str = "*.py") -> List[str]:
        """List files in a directory"""
        try:
            if directory:
                search_path = self.base_path / directory
            else:
                search_path = self.base_path
            
            files = list(search_path.rglob(pattern))
            return [str(f.relative_to(self.base_path)) for f in files[:50]]  # Limit to 50 files
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze a Python file for issues, functions, classes, etc."""
        try:
            full_path = self.base_path / file_path
            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            content = full_path.read_text()
            
            # Basic analysis
            lines = content.split('\n')
            functions = [line for line in lines if line.strip().startswith('def ')]
            classes = [line for line in lines if line.strip().startswith('class ')]
            imports = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
            
            return {
                "file_path": file_path,
                "total_lines": len(lines),
                "functions": len(functions),
                "classes": len(classes),
                "imports": len(imports),
                "function_names": [f.split('(')[0].replace('def ', '').strip() for f in functions],
                "class_names": [c.split(':')[0].replace('class ', '').strip() for c in classes]
            }
        except Exception as e:
            return {"error": f"Failed to analyze code: {e}"}
    
    def search_code(self, query: str, file_pattern: str = "*.py") -> List[Dict[str, Any]]:
        """Search for text in code files"""
        try:
            results = []
            files = self.list_files(pattern=file_pattern)
            
            for file_path in files[:20]:  # Limit search scope
                try:
                    full_path = self.base_path / file_path
                    content = full_path.read_text()
                    
                    if query.lower() in content.lower():
                        lines = content.split('\n')
                        matching_lines = []
                        for i, line in enumerate(lines):
                            if query.lower() in line.lower():
                                matching_lines.append({"line_number": i + 1, "content": line.strip()})
                        
                        if matching_lines:
                            results.append({
                                "file_path": file_path,
                                "matches": len(matching_lines),
                                "matching_lines": matching_lines[:5]  # Limit to 5 matches per file
                            })
                except Exception as e:
                    continue
            
            return results
        except Exception as e:
            logger.error(f"Failed to search code: {e}")
            return []
    
    def execute_script(self, script_path: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute a Python script"""
        try:
            full_path = self.base_path / script_path
            if not full_path.exists():
                return {"error": f"Script not found: {script_path}"}
            
            cmd = [sys.executable, str(full_path)]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.base_path)
            )
            
            return {
                "script_path": script_path,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Script execution timed out"}
        except Exception as e:
            return {"error": f"Failed to execute script: {e}"}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the current system and codebase"""
        try:
            return {
                "base_path": str(self.base_path),
                "python_version": sys.version,
                "total_python_files": len(self.list_files(pattern="*.py")),
                "services_directory": str(self.base_path / "services"),
                "scripts_directory": str(self.base_path / "scripts"),
                "agi_core_directory": str(self.base_path / "agi_core")
            }
        except Exception as e:
            return {"error": f"Failed to get system info: {e}"}

# Convenience function for quick access
def code_access(file_path: str = None, action: str = "read", **kwargs) -> Any:
    """
    Quick code access function
    
    Args:
        file_path: Path to file (relative to base_path)
        action: Action to perform (read, analyze, search, list, execute, info)
        **kwargs: Additional arguments for the action
    """
    tool = CodeAccessTool()
    
    if action == "read":
        return tool.read_file(file_path)
    elif action == "analyze":
        return tool.analyze_code(file_path)
    elif action == "search":
        return tool.search_code(kwargs.get('query', ''))
    elif action == "list":
        return tool.list_files(kwargs.get('directory', ''), kwargs.get('pattern', '*.py'))
    elif action == "execute":
        return tool.execute_script(file_path, kwargs.get('args', []))
    elif action == "info":
        return tool.get_system_info()
    else:
        return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
    # Test the tool
    tool = CodeAccessTool()
    
    print("Code Access Tool Test")
    print("=" * 30)
    
    # Test system info
    info = tool.get_system_info()
    print(f"System Info: {info}")
    
    # Test listing files
    files = tool.list_files("services", "*.py")
    print(f"Python files in services: {len(files)}")
    
    # Test reading a file
    if files:
        file_info = tool.read_file(files[0])
        print(f"First file: {file_info.get('file_path')} - {file_info.get('lines')} lines")

