#!/bin/bash
# AGI Core Wrapper - Makes Python process appear as Docker service
cd /Users/christianmerrill/Documents/GitHub
python3 -m uvicorn agi_core.agi_service:app --host 0.0.0.0 --port 8100 --reload
