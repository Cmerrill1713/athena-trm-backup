#!/usr/bin/env python3
"""
Test Graph-of-Code Service
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.goc.app import GraphDatabase


def test_database_initialization():
    """Test that database initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        assert db.conn is not None
        assert os.path.exists(db_path)
        print("✓ Database initialization")
        
        db.conn.close()


def test_add_symbol():
    """Test adding symbols to the graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        db.add_symbol("MyClass", "class", "test.py", 10, "python")
        db.add_symbol("my_function", "function", "test.py", 20, "python")
        
        assert db.get_symbol_count() == 2
        print("✓ Add symbols")
        
        db.conn.close()


def test_add_dependency():
    """Test adding dependencies to the graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        # Add symbols first
        db.add_symbol("caller", "function", "test.py", 10, "python")
        db.add_symbol("callee", "function", "test.py", 20, "python")
        
        # Add dependency
        db.add_dependency("caller", "callee", "calls")
        
        assert db.get_dependency_count() == 1
        print("✓ Add dependencies")
        
        db.conn.close()


def test_get_direct_dependents():
    """Test getting direct dependents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        # Build graph: A -> B -> C
        db.add_symbol("A", "function", "test.py", 10, "python")
        db.add_symbol("B", "function", "test.py", 20, "python")
        db.add_symbol("C", "function", "test.py", 30, "python")
        
        db.add_dependency("B", "A", "calls")  # B depends on A
        db.add_dependency("C", "B", "calls")  # C depends on B
        
        # Get direct dependents of A
        dependents = db.get_direct_dependents("A")
        assert "B" in dependents
        assert "C" not in dependents  # C is transitive, not direct
        
        print("✓ Get direct dependents")
        
        db.conn.close()


def test_get_transitive_dependents():
    """Test getting transitive dependents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        # Build graph: A -> B -> C -> D
        db.add_symbol("A", "function", "test.py", 10, "python")
        db.add_symbol("B", "function", "test.py", 20, "python")
        db.add_symbol("C", "function", "test.py", 30, "python")
        db.add_symbol("D", "function", "test.py", 40, "python")
        
        db.add_dependency("B", "A", "calls")
        db.add_dependency("C", "B", "calls")
        db.add_dependency("D", "C", "calls")
        
        # Get transitive dependents of A
        transitive = db.get_transitive_dependents("A")
        assert "B" in transitive
        assert "C" in transitive
        assert "D" in transitive
        
        print("✓ Get transitive dependents")
        
        db.conn.close()


def test_python_ingestor():
    """Test Python code ingestion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test Python file
        test_file = os.path.join(tmpdir, "test_code.py")
        with open(test_file, 'w') as f:
            f.write("""
def function_a():
    pass

def function_b():
    function_a()

class MyClass:
    def method_a(self):
        function_b()
""")
        
        # Create database
        db_path = os.path.join(tmpdir, "test_graph.db")
        db = GraphDatabase(db_path)
        
        # Ingest file
        from services.goc.ingestors.python_ingestor import PythonIngestor
        ingestor = PythonIngestor(db)
        stats = ingestor.ingest_files([test_file])
        
        assert stats['symbols_added'] > 0
        assert db.get_symbol_count() > 0
        
        print(f"✓ Python ingestion ({stats['symbols_added']} symbols, {stats['dependencies_added']} deps)")
        
        db.conn.close()


def main():
    """Run all tests."""
    print("🧪 Testing Graph-of-Code Service\n")
    print("=" * 60)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Add Symbol", test_add_symbol),
        ("Add Dependency", test_add_dependency),
        ("Get Direct Dependents", test_get_direct_dependents),
        ("Get Transitive Dependents", test_get_transitive_dependents),
        ("Python Ingestor", test_python_ingestor),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 60)
        try:
            test_func()
            passed += 1
            print("✅ PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}\n")
    
    print("=" * 60)
    print(f"\n📊 Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed == 0:
        print("🎉 All tests passed! Graph-of-Code service validated.")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

