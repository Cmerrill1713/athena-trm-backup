#!/usr/bin/env python3
"""
Python Code Ingestor for Graph-of-Code
Uses ast module to parse Python files and extract symbols/dependencies.
"""

import ast
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PythonIngestor:
    """Ingests Python files to build symbol graph."""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
        self.current_file = None
        self.symbols_added = 0
        self.dependencies_added = 0
    
    def ingest_files(self, files: List[str], project_root: str = None) -> Dict[str, int]:
        """Ingest multiple Python files."""
        self.symbols_added = 0
        self.dependencies_added = 0
        
        for file_path in files:
            try:
                self.ingest_file(file_path, project_root)
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
        
        return {
            "symbols_added": self.symbols_added,
            "dependencies_added": self.dependencies_added
        }
    
    def ingest_file(self, file_path: str, project_root: str = None):
        """Ingest a single Python file."""
        self.current_file = file_path
        
        # Read file
        with open(file_path, 'r') as f:
            source = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return
        
        # Extract symbols and dependencies
        visitor = PythonSymbolVisitor(self.graph_db, file_path)
        visitor.visit(tree)
        
        self.symbols_added += visitor.symbols_added
        self.dependencies_added += visitor.dependencies_added


class PythonSymbolVisitor(ast.NodeVisitor):
    """AST visitor to extract symbols and dependencies."""
    
    def __init__(self, graph_db, file_path: str):
        self.graph_db = graph_db
        self.file_path = file_path
        self.current_class = None
        self.current_function = None
        self.symbols_added = 0
        self.dependencies_added = 0
    
    def _get_fully_qualified_name(self, name: str) -> str:
        """Get fully qualified symbol name."""
        parts = []
        if self.current_class:
            parts.append(self.current_class)
        if self.current_function and not self.current_class:
            parts.append(self.current_function)
        parts.append(name)
        return ".".join(parts)
    
    def _add_symbol(self, symbol: str, kind: str, line: int, signature: str = ""):
        """Add a symbol to the graph."""
        self.graph_db.add_symbol(
            symbol=symbol,
            kind=kind,
            file=self.file_path,
            line=line,
            language="python",
            signature=signature
        )
        self.symbols_added += 1
    
    def _add_dependency(self, source: str, target: str, edge_type: str):
        """Add a dependency to the graph."""
        self.graph_db.add_dependency(source, target, edge_type)
        self.dependencies_added += 1
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        class_name = self._get_fully_qualified_name(node.name)
        self._add_symbol(class_name, "class", node.lineno)
        
        # Add inheritance dependencies
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                self._add_dependency(class_name, base_name, "inherits")
        
        # Visit class body
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function/method definition."""
        func_name = self._get_fully_qualified_name(node.name)
        kind = "method" if self.current_class else "function"
        
        # Build signature
        args = [arg.arg for arg in node.args.args]
        signature = f"{node.name}({', '.join(args)})"
        
        self._add_symbol(func_name, kind, node.lineno, signature)
        
        # Visit function body
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)  # Treat same as regular function
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        # Get caller context
        caller = None
        if self.current_function:
            caller = self._get_fully_qualified_name(self.current_function)
        elif self.current_class:
            caller = self.current_class
        
        # Get callee name
        callee = None
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        
        if caller and callee:
            self._add_dependency(caller, callee, "calls")
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            module_name = alias.name
            
            # Add dependency from file to imported module
            if self.current_function:
                source = self._get_fully_qualified_name(self.current_function)
            elif self.current_class:
                source = self.current_class
            else:
                source = self.file_path
            
            self._add_dependency(source, module_name, "imports")
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statement."""
        if node.module:
            for alias in node.names:
                symbol_name = f"{node.module}.{alias.name}"
                
                # Add dependency
                if self.current_function:
                    source = self._get_fully_qualified_name(self.current_function)
                elif self.current_class:
                    source = self.current_class
                else:
                    source = self.file_path
                
                self._add_dependency(source, symbol_name, "imports")

