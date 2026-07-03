import socketio
import asyncio
import time
import sys

sio = socketio.AsyncClient()
container_id = None
session_id = "test-session"

@sio.event
async def connect():
    print("Connected to server")
    await sio.emit("join-session", {"sessionId": session_id, "containerId": container_id, "username": "test"})

@sio.on("terminal-data")
async def on_terminal_data(data):
    print(f"TERMINAL: {repr(data)}")

@sio.event
async def disconnect():
    print("Disconnected from server")

async def main():
    global container_id
    if len(sys.argv) > 1:
        container_id = sys.argv[1]
    else:
        print("Need container_id")
        return
        
    await sio.connect('http://localhost:8000', transports=['websocket'])
    await asyncio.sleep(1)
    print("Sending 'l'...")
    await sio.emit("terminal-input", "l")
    await asyncio.sleep(0.5)
    print("Sending 's'...")
    await sio.emit("terminal-input", "s")
    await asyncio.sleep(0.5)
    print("Sending '\\r'...")
    await sio.emit("terminal-input", "\r")
    await asyncio.sleep(2)
    await sio.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
