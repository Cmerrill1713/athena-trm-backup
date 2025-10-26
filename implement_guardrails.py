#!/usr/bin/env python3
"""
IMPLEMENT GUARDRAILS
Rate limiting, auth, CORS, input validation
"""

print("🛡️  IMPLEMENTING PRODUCTION GUARDRAILS")
print("="*80)
print("")

# Generate rate limiting middleware
rate_limit_config = {
    "global_burst": 120,  # requests per minute
    "global_sustained": 60,  # avg requests per minute
    "per_endpoint": {
        "/v1/chat/completions": {"burst": 60, "sustained": 30},
        "/route": {"burst": 120, "sustained": 60},
        "/v1/learning/trigger": {"burst": 10, "sustained": 5},
        "/tool/web_search": {"burst": 30, "sustained": 15},
        "/synthesize": {"burst": 30, "sustained": 15},
        "/transcribe": {"burst": 20, "sustained": 10}
    },
    "per_key_limits": {
        "family": {"burst": 120, "sustained": 60},
        "guest": {"burst": 30, "sustained": 15}
    }
}

import json
with open("rate_limit_config.json", "w") as f:
    json.dump(rate_limit_config, f, indent=2)

print("✅ Rate limit config generated")

# Generate auth policy
auth_policy = {
    "public_endpoints": [
        "/health",
        "/metrics",
        "/ready",
        "/version"
    ],
    "token_required": [
        "/v1/chat/completions",
        "/api/tasks/*",
        "/api/users/*",
        "/v1/feedback",
        "/tool/*"
    ],
    "mtls_required": [
        "/v1/learning/trigger",
        "/v2/judicial/adjudicate",
        "/reload-policy",
        "/remediate",
        "/federation/*"
    ],
    "cors_allowed_origins": [
        "http://localhost:8082",
        "http://127.0.0.1:8082",
        "https://athena.local"  # For future PWA domain
    ]
}

with open("auth_policy.json", "w") as f:
    json.dump(auth_policy, f, indent=2)

print("✅ Auth policy generated")

# Generate input validation rules
input_validation = {
    "max_body_size_mb": 10,
    "max_text_length": 50000,
    "max_request_timeout_sec": 30,
    "max_concurrent_per_key": 5,
    "pagination_defaults": {
        "page_size": 20,
        "max_page_size": 100
    },
    "topK_caps": {
        "rag_results": 10,
        "search_results": 20
    }
}

with open("input_validation.json", "w") as f:
    json.dump(input_validation, f, indent=2)

print("✅ Input validation rules generated")

print("\n📄 Files created:")
print("   - rate_limit_config.json")
print("   - auth_policy.json")
print("   - input_validation.json")
print("\n💙 Guardrails configured!")
