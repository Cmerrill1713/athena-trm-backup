#!/usr/bin/env python3
"""
GATEWAY DENYLIST GENERATOR
Identify and block deprecated/broken endpoints
"""
import json

# Broken/stale endpoints to deprecate (30% = ~50 endpoints)
deprecated_endpoints = []

print("🚫 GENERATING GATEWAY DENYLIST")
print("="*80)
print("")

# From our testing, these are failing or unused
deprecated = [
    # UAI - Broken
    {"path": "/api/security/encrypt", "reason": "Not implemented", "alternative": "Use TLS"},
    {"path": "/api/security/detect_pii", "reason": "Not implemented", "alternative": "Use Presidio directly"},
    {"path": "/v1/rag/historical", "reason": "Not implemented", "alternative": "Use /v1/chat/completions with RAG"},
    
    # Router - Unused
    {"path": "/respond", "reason": "Duplicate of /route", "alternative": "/route"},
    
    # Federation - Not ready
    {"path": "/federation/register", "reason": "Not implemented", "alternative": "Contact admin"},
    {"path": "/federation/sync", "reason": "Not implemented", "alternative": "Automatic sync"},
    {"path": "/federation/consensus", "reason": "Not implemented", "alternative": "Judicial adjudicate"},
    {"path": "/federation/vote", "reason": "Not implemented", "alternative": "Judicial adjudicate"},
    {"path": "/federation/reputation/*", "reason": "Not implemented", "alternative": "Coming soon"},
    
    # Judicial - Wrong endpoint
    {"path": "/v2/adjudicate", "reason": "Wrong path", "alternative": "/v2/judicial/adjudicate"},
    {"path": "/v2/audit", "reason": "Not implemented", "alternative": "Check logs"},
    
    # MCP - Broken tools
    {"path": "/tool/calculator", "reason": "Not implemented", "alternative": "Ask in chat"},
    {"path": "/tool/wikipedia_search", "reason": "Use web_search", "alternative": "/tool/web_search"},
    
    # macOS Bridge - Not working in Docker
    {"path": "/calendar/add_event", "reason": "AppleScript in Docker fails", "alternative": "Use MCP calendar_add proxy"},
    {"path": "/calendar/list_events", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    {"path": "/reminders/add", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    {"path": "/notes/create", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    {"path": "/messages/send", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    {"path": "/app/launch", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    {"path": "/app/install", "reason": "AppleScript in Docker fails", "alternative": "Use MCP proxy"},
    
    # AGI Core - Not implemented
    {"path": "/execute", "reason": "Not implemented", "alternative": "Use /tools"},
    {"path": "/workflows", "reason": "Not implemented", "alternative": "Coming soon"},
    {"path": "/remediate", "reason": "Not implemented", "alternative": "Auto-remediation active"},
    
    # Learning - Not implemented
    {"path": "/v1/learning/status", "reason": "Use /health", "alternative": "/health"},
    {"path": "/v1/learning/metrics", "reason": "Use /metrics", "alternative": "/metrics"},
    
    # Governance - Not implemented
    {"path": "/policies", "reason": "Not implemented", "alternative": "Contact admin"},
    {"path": "/evaluate", "reason": "Not implemented", "alternative": "Automatic evaluation"},
]

for item in deprecated:
    deprecated_endpoints.append({
        "path": item["path"],
        "service": "multiple",
        "status": "deprecated",
        "http_code": 410,  # Gone
        "reason": item["reason"],
        "alternative": item["alternative"],
        "sunset_date": "2025-11-26",  # 30 days from now
        "contact": "christian@athena"
    })

print(f"Added {len(deprecated_endpoints)} deprecated endpoints")

# Save as JSON
with open("gateway_denylist.json", "w") as f:
    json.dump(deprecated_endpoints, f, indent=2)

# Generate nginx/gateway config snippet
with open("gateway_denylist.conf", "w") as f:
    f.write("# Athena Gateway Denylist - Auto-generated\n")
    f.write("# Blocks deprecated endpoints with 410 Gone\n\n")
    
    for endpoint in deprecated_endpoints:
        path = endpoint["path"]
        reason = endpoint["reason"]
        alternative = endpoint["alternative"]
        
        f.write(f"# {path} - {reason}\n")
        f.write(f"location ~ ^{path.replace('*', '.*')} {{\n")
        f.write(f'    return 410 "{reason}. Use: {alternative}";\n')
        f.write("}\n\n")

print("\n📄 Saved to:")
print("   - gateway_denylist.json")
print("   - gateway_denylist.conf (nginx)")
print(f"\n🚫 Will block {len(deprecated_endpoints)} deprecated endpoints")
print("💙 Gateway denylist complete!")
