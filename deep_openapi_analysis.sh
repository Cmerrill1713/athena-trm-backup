#!/bin/bash
echo "🔍 DEEP OPENAPI ANALYSIS - Every Endpoint"
echo "========================================================================"
echo ""

total_endpoints=0

# Services with OpenAPI
services=(
    "8080:UAI"
    "9113:Router"
    "8098:Learning"
    "8091:Kokoro"
    "8095:Whisper"
    "8088:FastVLM"
    "8096:Judicial"
    "8097:Federation"
    "8412:MCP"
    "9110:Governance"
    "9109:Gov-Metrics"
    "9111:Canary"
)

for service in "${services[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$name (Port $port)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get OpenAPI spec
    spec=$(curl -s http://localhost:$port/openapi.json 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$spec" ]; then
        # Extract all paths
        paths=$(echo "$spec" | jq -r '.paths | keys[]' 2>/dev/null)
        
        if [ ! -z "$paths" ]; then
            count=$(echo "$paths" | wc -l)
            echo "  Found $count endpoints:"
            echo "$paths" | while read path; do
                # Get methods for this path
                methods=$(echo "$spec" | jq -r ".paths[\"$path\"] | keys[]" 2>/dev/null)
                echo "    $path: $(echo $methods | tr '\n' ',' | sed 's/,$//')"
            done
            ((total_endpoints += count))
        else
            echo "  ⚠️  No paths found in OpenAPI"
        fi
    else
        echo "  ⚠️  No OpenAPI spec available"
    fi
    echo ""
done

echo "========================================================================"
echo "📊 TOTAL ENDPOINTS IN OPENAPI SPECS: $total_endpoints"
echo "========================================================================"
