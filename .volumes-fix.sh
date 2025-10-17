#!/bin/bash
# Fix volumes to be external
sed -i '' '/postgres_data:/a\
    external: true
' docker-compose.yml
sed -i '' '/redis_data:/a\
    external: true
' docker-compose.yml
sed -i '' '/weaviate_data:/a\
    external: true
' docker-compose.yml
sed -i '' '/prometheus_data:/a\
    external: true
' docker-compose.yml
sed -i '' '/grafana_data:/a\
    external: true
' docker-compose.yml
sed -i '' '/netdata_config:/a\
    external: true
' docker-compose.yml
sed -i '' '/netdata_lib:/a\
    external: true
' docker-compose.yml
sed -i '' '/netdata_cache:/a\
    external: true
' docker-compose.yml

