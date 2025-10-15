#!/usr/bin/env python3
"""
Tracing Integration Helper
Adds OpenTelemetry tracing and structured logging to Python services
"""

import re
from pathlib import Path

def integrate_tracing_in_bridge():
    """Add tracing to Bridge adapter.py"""
    bridge_file = Path("bridge/adapter.py")

    if not bridge_file.exists():
        print("❌ Bridge adapter.py not found")
        return False

    content = bridge_file.read_text()

    # Check if already integrated
    if "from common.tracing import" in content:
        print("✅ Bridge already has tracing integration")
        return True

    # Add imports after existing imports
    import_pattern = r'(import.*\n)+'
    tracing_imports = '''from common.tracing import init_tracing, instrument_fastapi, get_tracer, traced
from common.logging import logger

'''

    # Find where to insert imports (after the last import)
    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + tracing_imports + content[insert_pos:]

    # Add tracing initialization after app creation
    app_pattern = r'(app = FastAPI\([^)]*\))'
    init_code = '''

# Initialize tracing
init_tracing("bridge")

# Instrument FastAPI
instrument_fastapi(app)

# Add structured logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    with get_tracer(__name__).start_as_current_span("http_request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))

        response = await call_next(request)

        span.set_attribute("http.status_code", response.status_code)
        logger.info("HTTP request", {
            "method": request.method,
            "url": str(request.url),
            "status": response.status_code
        })

        return response

'''

    content = re.sub(app_pattern, r'\1' + init_code, content)

    # Add tracing to chat endpoint
    chat_pattern = r'(@app\.post\("/chat"\)\s*async def chat\()'
    traced_chat = '''@app.post("/chat")
@traced("chat_endpoint")
async def chat('''

    content = re.sub(chat_pattern, traced_chat, content)

    bridge_file.write_text(content)
    print("✅ Integrated tracing into Bridge")
    return True

def integrate_tracing_in_athena():
    """Add tracing to Athena api.py"""
    athena_file = Path("AI-Projects/universal-ai-tools/athena/api.py")

    if not athena_file.exists():
        print("❌ Athena api.py not found")
        return False

    content = athena_file.read_text()

    # Check if already integrated
    if "from common.tracing import" in content:
        print("✅ Athena already has tracing integration")
        return True

    # Add imports
    import_pattern = r'(import.*\n)+'
    tracing_imports = '''from common.tracing import init_tracing, instrument_fastapi, get_tracer, traced
from common.logging import logger

'''

    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + tracing_imports + content[insert_pos:]

    # Add tracing initialization
    app_pattern = r'(app = FastAPI\([^)]*\))'
    init_code = '''

# Initialize tracing
init_tracing("athena")

# Instrument FastAPI
instrument_fastapi(app)

'''

    content = re.sub(app_pattern, r'\1' + init_code, content)

    # Add tracing to chat endpoint
    chat_pattern = r'(@app\.post\("/chat"\)\s*async def chat\()'
    traced_chat = '''@app.post("/chat")
@traced("athena_chat")
async def chat('''

    content = re.sub(chat_pattern, traced_chat, content)

    athena_file.write_text(content)
    print("✅ Integrated tracing into Athena")
    return True

def integrate_tracing_in_rag():
    """Add tracing to RAG service.py"""
    rag_file = Path("AI-Projects/universal-ai-tools/rag_service.py")

    if not rag_file.exists():
        print("❌ RAG service.py not found")
        return False

    content = rag_file.read_text()

    # Check if already integrated
    if "from common.tracing import" in content:
        print("✅ RAG already has tracing integration")
        return True

    # Add imports
    import_pattern = r'(import.*\n)+'
    tracing_imports = '''from common.tracing import init_tracing, instrument_fastapi, traced
from common.logging import logger

'''

    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + tracing_imports + content[insert_pos:]

    # Add tracing initialization
    app_pattern = r'(app = FastAPI\([^)]*\))'
    init_code = '''

# Initialize tracing
init_tracing("rag")

# Instrument FastAPI
instrument_fastapi(app)

'''

    content = re.sub(app_pattern, r'\1' + init_code, content)

    # Add tracing to query endpoint
    query_pattern = r'(@app\.post\("/query"\)\s*async def rag_query\()'
    traced_query = '''@app.post("/query")
@traced("rag_query")
async def rag_query('''

    content = re.sub(query_pattern, traced_query, content)

    rag_file.write_text(content)
    print("✅ Integrated tracing into RAG")
    return True

def integrate_tracing_in_vision():
    """Add tracing to Vision service.py"""
    vision_file = Path("AI-Projects/universal-ai-tools/vision_rag_service.py")

    if not vision_file.exists():
        print("❌ Vision service.py not found")
        return False

    content = vision_file.read_text()

    # Check if already integrated
    if "from common.tracing import" in content:
        print("✅ Vision already has tracing integration")
        return True

    # Add imports
    import_pattern = r'(import.*\n)+'
    tracing_imports = '''from common.tracing import init_tracing, instrument_fastapi, traced
from common.logging import logger

'''

    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + tracing_imports + content[insert_pos:]

    # Add tracing initialization
    app_pattern = r'(app = FastAPI\([^)]*\))'
    init_code = '''

# Initialize tracing
init_tracing("vision")

# Instrument FastAPI
instrument_fastapi(app)

'''

    content = re.sub(app_pattern, r'\1' + init_code, content)

    # Add tracing to vision endpoints
    vision_pattern = r'(@app\.post\("/api/vision/describe"\)\s*async def vision_describe\()'
    traced_vision = '''@app.post("/api/vision/describe")
@traced("vision_describe")
async def vision_describe('''

    content = re.sub(vision_pattern, traced_vision, content)

    vision_file.write_text(content)
    print("✅ Integrated tracing into Vision")
    return True

def integrate_tracing_in_kokoro():
    """Add tracing to Kokoro service.py"""
    kokoro_file = Path("kokoro/kokoro_tts_service.py")

    if not kokoro_file.exists():
        print("❌ Kokoro service.py not found")
        return False

    content = kokoro_file.read_text()

    # Check if already integrated
    if "from common.tracing import" in content:
        print("✅ Kokoro already has tracing integration")
        return True

    # Add imports
    import_pattern = r'(import.*\n)+'
    tracing_imports = '''from common.tracing import init_tracing, instrument_fastapi, traced
from common.logging import logger

'''

    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + tracing_imports + content[insert_pos:]

    # Add tracing initialization
    app_pattern = r'(app = FastAPI\([^)]*\))'
    init_code = '''

# Initialize tracing
init_tracing("kokoro")

# Instrument FastAPI
instrument_fastapi(app)

'''

    content = re.sub(app_pattern, r'\1' + init_code, content)

    # Add tracing to synthesize endpoint
    tts_pattern = r'(@app\.post\("/synthesize"\)\s*async def synthesize\()'
    traced_tts = '''@app.post("/synthesize")
@traced("tts_synthesize")
async def synthesize('''

    content = re.sub(tts_pattern, traced_tts, content)

    kokoro_file.write_text(content)
    print("✅ Integrated tracing into Kokoro")
    return True

def main():
    """Integrate tracing into all services"""
    print("🔧 Integrating OpenTelemetry tracing into services...")
    print("=" * 60)

    services = [
        integrate_tracing_in_bridge,
        integrate_tracing_in_athena,
        integrate_tracing_in_rag,
        integrate_tracing_in_vision,
        integrate_tracing_in_kokoro,
    ]

    success_count = 0
    for service_func in services:
        try:
            if service_func():
                success_count += 1
        except Exception as e:
            print(f"❌ Error integrating {service_func.__name__}: {e}")

    print("=" * 60)
    print(f"✅ Successfully integrated tracing into {success_count}/{len(services)} services")

    if success_count == len(services):
        print("\n🚀 Next steps:")
        print("1. Restart your services to pick up tracing changes")
        print("2. Run: make addons-up")
        print("3. Check Grafana Tempo for traces")
        print("4. Check Loki for structured logs")

if __name__ == "__main__":
    main()
