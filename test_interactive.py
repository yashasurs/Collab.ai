import socketio
import asyncio
import sys
import tty
import termios

sio = socketio.AsyncClient()
container_id = None
session_id = "test-session"

@sio.event
async def connect():
    print("\r\nConnected to server\r")
    await sio.emit("join-session", {"sessionId": session_id, "containerId": container_id, "username": "test"})

@sio.on("terminal-data")
async def on_terminal_data(data):
    sys.stdout.write(data)
    sys.stdout.flush()

@sio.event
async def disconnect():
    print("\r\nDisconnected from server\r")

async def read_input():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            # Read single character
            ch = sys.stdin.read(1)
            if ch == '\x03': # Ctrl+C
                break
            await sio.emit("terminal-input", ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        await sio.disconnect()

async def main():
    global container_id
    if len(sys.argv) > 1:
        container_id = sys.argv[1]
    else:
        print("Need container_id")
        return
        
    await sio.connect('http://localhost:8000', transports=['websocket'])
    await read_input()

if __name__ == '__main__':
    asyncio.run(main())
