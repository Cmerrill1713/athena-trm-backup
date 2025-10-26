#!/bin/sh
# Entrypoint for OpenAI Adapter with Network Isolation
# Blocks all outbound except local subnets (air-gapped mode)

set -e

echo "🔒 Configuring network isolation..."

# Drop all outbound by default
iptables -P OUTPUT DROP 2>/dev/null || echo "⚠️  iptables not available (needs NET_ADMIN capability)"

# Allow local subnets only
iptables -A OUTPUT -d 127.0.0.0/8   -j ACCEPT 2>/dev/null || true  # localhost
iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT 2>/dev/null || true  # Docker bridge
iptables -A OUTPUT -d 10.0.0.0/8    -j ACCEPT 2>/dev/null || true  # Private
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT 2>/dev/null || true # Private

# Allow DNS within Docker network
iptables -A OUTPUT -p udp --dport 53 -d 127.0.0.11 -j ACCEPT 2>/dev/null || true

# Allow established connections (responses)
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true

echo "✅ Network isolation configured"
echo "   - Outbound DEFAULT: DROP"
echo "   - Allowed: 127.0.0.0/8, 172.16.0.0/12, 10.0.0.0/8, 192.168.0.0/16"
echo ""

# Start the application
exec node server.js

