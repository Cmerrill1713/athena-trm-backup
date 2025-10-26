#!/bin/bash
AR_HOME="/home/developer/.local/share/ai-republic"
cd "$AR_HOME" && export PYTHONPATH="$AR_HOME:/app" && bash run_tests.sh
