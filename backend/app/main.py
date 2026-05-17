import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import socketio
from app.routers import sessions, ai_agent, containers, tunnels, auth, snapshots
from app.core.terminal_manager import terminal_manager
from app.database.database import engine
from app.models.models import Base

Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI(title="Ghost Labs Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(ai_agent.router, prefix="/api/ai", tags=["ai"])
app.include_router(containers.router, prefix="/api/containers", tags=["containers"])
app.include_router(tunnels.router, prefix="/api/tunnels", tags=["tunnels"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(snapshots.router, prefix="/api/snapshots", tags=["snapshots"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Ghost Labs Monolithic API is running"}

# Session participant tracking
session_participants = {} # sessionId -> [ {sid, username} ]

# Socket.io event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.on("join-session")
async def handle_join_session(sid, data):
    session_id = data.get("sessionId")
    username = data.get("username", "Anonymous")
    container_id = data.get("containerId")
    
    await sio.enter_room(sid, session_id)
    
    # Track participant
    if session_id not in session_participants:
        session_participants[session_id] = []
    
    # Avoid duplicates if reconnecting
    session_participants[session_id] = [p for p in session_participants[session_id] if p['sid'] != sid]
    session_participants[session_id].append({"sid": sid, "username": username})
    
    # Notify everyone in the room about the new participant
    await sio.emit("participants-update", session_participants[session_id], room=session_id)
    await sio.emit("user-joined-webrtc", sid, room=session_id, skip_sid=sid)
    
    if container_id:
        async def on_terminal_data(target_sid, output_data):
            await sio.emit("terminal-data", output_data.decode(errors='replace'), to=target_sid)
        await terminal_manager.create_terminal_socket(container_id, sid, on_terminal_data)

@sio.on("terminal-input")
async def handle_terminal_input(sid, data):
    terminal_manager.write_to_terminal(sid, data)

@sio.on("editor-change")
async def handle_editor_change(sid, data):
    session_id = data.get("sessionId")
    await sio.emit("editor-sync", data, room=session_id, skip_sid=sid)

# WebRTC Signaling
@sio.on("webrtc-offer")
async def handle_webrtc_offer(sid, data):
    await sio.emit("webrtc-offer", {"from": sid, "offer": data["offer"]}, to=data["to"])

@sio.on("webrtc-answer")
async def handle_webrtc_answer(sid, data):
    await sio.emit("webrtc-answer", {"from": sid, "answer": data["answer"]}, to=data["to"])

@sio.on("webrtc-ice-candidate")
async def handle_webrtc_ice_candidate(sid, data):
    await sio.emit("webrtc-ice-candidate", {"from": sid, "candidate": data["candidate"]}, to=data["to"])

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    terminal_manager.close_terminal(sid)
    
    # Remove from participants
    for session_id, participants in session_participants.items():
        if any(p['sid'] == sid for p in participants):
            session_participants[session_id] = [p for p in participants if p['sid'] != sid]
            await sio.emit("participants-update", session_participants[session_id], room=session_id)
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
