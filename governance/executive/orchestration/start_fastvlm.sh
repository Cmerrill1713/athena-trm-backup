#!/usr/bin/env bash
# FastVLM Startup Script with Python 3.11

# Change to script directory
cd "$(dirname "$0")"

# Activate Python 3.11 venv
source ~/.venvs/fastvlm311/bin/activate

# Set environment variables (using absolute paths)
export FASTVLM_ROOT="$(pwd)/ml-fastvlm"
export FASTVLM_MODEL="checkpoints/llava-fastvithd_1.5b_stage3"
export ENV="prod"
export BUILD_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
export FASTVLM_HOST="127.0.0.1"
export FASTVLM_PORT="8811"

# Start server
python fastvlm_server.py
