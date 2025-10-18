# Graph-of-Code (GoC) Service

## 🎯 **Overview**

Graph-of-Code is a symbol dependency graph service for impact analysis and test coverage queries. It builds a comprehensive graph of code symbols and their relationships, enabling developers to answer critical questions:

- **"Who breaks if I change X?"** - Impact analysis
- **"Which tests cover Y?"** - Test coverage mapping
- **"What depends on this symbol?"** - Dependency tracking

---

## 🚀 **Features**

### **Core Capabilities**

- ✅ Symbol dependency graph building
- ✅ Impact analysis (direct + transitive dependents)
- ✅ Test coverage mapping
- ✅ Multi-language support (Python implemented, Swift/Rust/Go stubs)
- ✅ SQLite storage for fast queries
- ✅ Prometheus metrics integration
- ✅ FastAPI REST endpoints

### **Supported Languages**

- ✅ **Python** - Full implementation using AST parsing
- ⚠️ **Swift** - Stub (use sourcekit-lsp or swift-syntax)
- ⚠️ **Rust** - Stub (use rust-analyzer)
- ⚠️ **Go** - Stub (use gopls)

---

## 📊 **Architecture**

### **Database Schema**

```sql
symbols (symbol, kind, file, line, language, signature)
dependencies (source, target, edge_type, weight)
tests (test_name, file, line, language)
test_coverage (test_name, symbol, coverage_type)
```

### **Ingestors**

Language-specific code parsers that extract symbols and dependencies:

- `PythonIngestor` - Uses Python `ast` module
- `SwiftIngestor` - Stub for sourcekit-lsp integration
- `RustIngestor` - Stub for rust-analyzer integration
- `GoIngestor` - Stub for gopls integration

---

## 🔧 **API Endpoints**

### **GET /**

Service information and status

### **GET /health**

Health check with symbol and dependency counts

### **POST /ingest**

Ingest code files to build the graph

```json
{
  "files": ["path/to/file1.py", "path/to/file2.py"],
  "language": "python",
  "project_root": "/path/to/project"
}
```

### **GET /impact?symbol=X**

Analyze impact of changing a symbol

```json
{
  "symbol": "my_function",
  "direct_dependents": ["caller1", "caller2"],
  "transitive_dependents": ["caller3", "caller4"],
  "affected_files": ["file1.py", "file2.py"],
  "affected_tests": ["test_file1.py::test_my_function"],
  "impact_score": 0.35,
  "timestamp": "2025-10-17T19:00:00Z"
}
```

### **GET /tests?file=Y**

Find tests covering a file

```json
{
  "file": "src/utils.py",
  "direct_tests": ["tests/test_utils.py::test_helper"],
  "indirect_tests": ["tests/test_integration.py::test_workflow"],
  "coverage_score": 0.85,
  "timestamp": "2025-10-17T19:00:00Z"
}
```

### **GET /metrics**

Prometheus metrics endpoint

---

## 🧪 **Testing**

### **Run Tests**

```bash
cd /Users/christianmerrill/Documents/GitHub
python3 services/goc/test_goc.py
```

### **Test Results**

```
✅ Database Initialization
✅ Add Symbol
✅ Add Dependency
✅ Get Direct Dependents
✅ Get Transitive Dependents
✅ Python Ingestor

📊 6/6 tests passed
```

---

## 🚀 **Quick Start**

### **1. Start the Service**

```bash
cd /Users/christianmerrill/Documents/GitHub
python3 services/goc/app.py
```

Service runs on `http://127.0.0.1:8200` by default.

### **2. Ingest Code**

```bash
curl -X POST http://127.0.0.1:8200/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "files": ["path/to/file.py"],
    "language": "python"
  }'
```

### **3. Query Impact**

```bash
curl 'http://127.0.0.1:8200/impact?symbol=my_function'
```

### **4. Query Test Coverage**

```bash
curl 'http://127.0.0.1:8200/tests?file=src/utils.py'
```

---

## 📈 **Metrics**

Prometheus metrics exposed at `/metrics`:

- `goc_symbols_total` - Total symbols in graph
- `goc_dependencies_total` - Total dependencies in graph
- `goc_ingest_duration_seconds` - Ingestion latency
- `goc_impact_queries_total` - Impact queries served
- `goc_test_queries_total` - Test coverage queries served

---

## 🔮 **Future Enhancements**

### **Language Support**

- [ ] Swift - Integrate sourcekit-lsp
- [ ] Rust - Integrate rust-analyzer
- [ ] Go - Integrate gopls
- [ ] TypeScript/JavaScript - Use TypeScript compiler API

### **Features**

- [ ] Call hierarchy visualization
- [ ] Circular dependency detection
- [ ] Code complexity metrics
- [ ] Change impact simulation
- [ ] Integration with CI/CD pipelines
- [ ] Graph export to Neo4j/GraphML

### **Performance**

- [ ] Incremental updates (only re-ingest changed files)
- [ ] Graph caching and indexing
- [ ] Distributed graph storage
- [ ] Parallel ingestion

---

## 📝 **Examples**

### **Example: Impact Analysis**

```python
# If I change function_a, what breaks?
GET /impact?symbol=function_a

Response:
{
  "direct_dependents": ["function_b", "function_c"],
  "transitive_dependents": ["function_d", "MyClass.method"],
  "affected_files": ["utils.py", "helpers.py", "main.py"],
  "affected_tests": ["test_utils.py", "test_integration.py"],
  "impact_score": 0.42  // 42% of codebase affected
}
```

### **Example: Test Coverage**

```python
# Which tests cover utils.py?
GET /tests?file=src/utils.py

Response:
{
  "direct_tests": [
    "tests/test_utils.py::test_helper",
    "tests/test_utils.py::test_validator"
  ],
  "indirect_tests": [
    "tests/test_integration.py::test_workflow"
  ],
  "coverage_score": 0.85  // 85% of symbols have test coverage
}
```

---

## 🏆 **Status**

**Current:** B2 (Graph-of-Code MVP) - ✅ **COMPLETE**

- ✅ Core service implemented (FastAPI)
- ✅ SQLite database with symbol/dependency schema
- ✅ Python ingestor using AST parsing
- ✅ Impact analysis (direct + transitive)
- ✅ Test coverage queries
- ✅ Prometheus metrics
- ✅ 6/6 tests passing

**Next Steps:**

- Implement Swift/Rust/Go ingestors
- Add incremental update support
- Integrate with CI/CD
- Add visualization dashboard

---

_Graph-of-Code service built on 2025-10-17. Part of the Athena ecosystem._
