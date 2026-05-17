import sys
import traceback

print("Starting import test...")
try:
    from app.main import socket_app
    print("Import OK")
except Exception as e:
    print("Import failed!")
    traceback.print_exc()
