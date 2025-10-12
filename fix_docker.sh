#!/bin/bash
# Docker Desktop Fix Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Docker Desktop Repair Script                      ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""
echo "Detected issues:"
echo "  ❌ Docker VM disk: 141GB (very large)"
echo "  ❌ 'no space left on device' errors"
echo "  ❌ I/O errors in container storage"
echo ""

echo "Choose repair option:"
echo "  1. Clean Docker (keeps your data, removes unused)"
echo "  2. Reset Docker VM (deletes containers, fresh start)"
echo "  3. Full factory reset (complete clean slate)"
echo "  4. Just restart (try again)"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
  1)
    echo "Quitting Docker..."
    osascript -e 'quit app "Docker"'
    sleep 3
    
    echo "Starting Docker for cleanup..."
    open -a Docker
    sleep 20
    
    echo "Cleaning Docker system..."
    docker system prune -a --volumes -f
    
    echo "✓ Cleanup complete!"
    echo "Restarting Docker..."
    osascript -e 'quit app "Docker"'
    sleep 3
    open -a Docker
    ;;
    
  2)
    echo "⚠️  This will delete all containers and images!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
      echo "Quitting Docker..."
      killall "Docker Desktop" 2>/dev/null
      sleep 3
      
      echo "Removing Docker VM..."
      rm -rf ~/Library/Containers/com.docker.docker/Data/vms
      
      echo "Starting Docker (will recreate VM)..."
      open -a Docker
      
      echo "✓ VM reset! Wait 1-2 minutes for Docker to start"
    fi
    ;;
    
  3)
    echo "⚠️  This will delete EVERYTHING (containers, images, settings)!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
      echo "Quitting Docker..."
      killall "Docker Desktop" 2>/dev/null
      sleep 3
      
      echo "Factory reset..."
      rm -rf ~/Library/Containers/com.docker.docker
      rm -rf ~/Library/Group\ Containers/group.com.docker
      
      echo "Starting Docker fresh..."
      open -a Docker
      
      echo "✓ Factory reset! Wait 2-3 minutes for initial setup"
    fi
    ;;
    
  4)
    echo "Restarting Docker..."
    killall "Docker Desktop" 2>/dev/null
    sleep 3
    open -a Docker
    echo "✓ Restarted! Wait 30 seconds..."
    ;;
    
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "Waiting for Docker to be ready..."
sleep 15

for i in {1..20}; do
  if docker ps >/dev/null 2>&1; then
    echo "✓ Docker is ready!"
    docker ps
    exit 0
  fi
  echo "  Waiting... ($i/20)"
  sleep 3
done

echo "⚠️  Docker still not ready. Try:"
echo "  1. Open Docker Desktop app manually"
echo "  2. Check menu bar icon for status"
echo "  3. Look for error messages in Docker Desktop UI"

