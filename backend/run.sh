#!/bin/bash
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000
