#!/usr/bin/env bash
set -euo pipefail
echo "🔒 PINNING CRITICAL IMAGE DIGESTS"
echo "=================================="
for img in prom/prometheus:latest grafana/grafana:latest prom/pushgateway:latest prom/alertmanager:latest; do
  echo "Pulling $img..."
  docker pull "$img" >/dev/null 2>&1 || echo "  (already pulled)"
  dig=$(docker image inspect "$img" -f '{{index .RepoDigests 0}}' 2>/dev/null || echo "")
  if [ -n "$dig" ]; then
    echo "$img -> $dig"
    repo=${dig%@sha256:*}
    sha=${dig#*@sha256:}
    echo "  image: ${repo}@sha256:${sha}"
    echo
  fi
done
echo "✅ Copy the 'image:' lines above into docker-compose.yml"
