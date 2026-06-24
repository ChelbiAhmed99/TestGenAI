#!/bin/bash
# Launch the backend using the virtual environment
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
