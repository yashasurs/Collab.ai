import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import socketio
from app.routers import sessions, ai_agent, containers, tunnels, auth, snapshots
from app.core.terminal_manager import terminal_manager
from app.database.database import engine, SessionLocal
from app.core.logging import setup_logging

load_dotenv()

# Initialize structured logging
setup_logging()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup: verify database connectivity
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    # Startup: verify Redis connectivity
    from app.core.redis import redis_health_check
    if await redis_health_check():
        logger.info("Redis connection verified")
    else:
        logger.warning("Redis unavailable — running without cross-replica sync")

    # Startup: tunnel broker background cleanup
    from app.services.tunnel_broker import tunnel_broker
    await tunnel_broker.start()

    yield

    # Shutdown: cleanup resources
    await tunnel_broker.stop()
    terminal_manager.close_all()
    engine.dispose()

    from app.core.redis import close_async_redis
    await close_async_redis()

    logger.info("Application shutdown complete")


app = FastAPI(title="Colab.ai Backend", lifespan=lifespan)

# CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Socket.io setup — Redis adapter for cross-replica event fan-out
# ---------------------------------------------------------------------------

_use_redis = bool(REDIS_URL and REDIS_URL != "none")

if _use_redis:
    try:
        mgr = socketio.AsyncRedisManager(REDIS_URL)
        sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            client_manager=mgr,
        )
        logger.info("Socket.io: using Redis adapter for cross-replica sync")
    except Exception as e:
        logger.warning(f"Socket.io Redis adapter failed ({e}), falling back to in-memory")
        sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
else:
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
    """Health check endpoint with subsystem status."""
    from app.core.redis import redis_health_check

    redis_ok = await redis_health_check()
    db_ok = True
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "message": "Colab.ai API is running",
        "subsystems": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }


# ---------------------------------------------------------------------------
# Socket.io event handlers — participant state now in Redis
# ---------------------------------------------------------------------------

@sio.event
async def connect(sid, environ):
    """Validate JWT before accepting WebSocket connection."""
    # Extract token from query string or auth header
    query_string = environ.get("QUERY_STRING", "")
    token = None

    # Try query string: ?token=xxx
    for param in query_string.split("&"):
        if param.startswith("token="):
            token = param.split("=", 1)[1]
            break

    # Try Authorization header
    if not token:
        headers = environ.get("HTTP_AUTHORIZATION", "")
        if headers.startswith("Bearer "):
            token = headers[7:]

    if token:
        try:
            from jose import jwt as jose_jwt
            from app.auth.security import SECRET_KEY, ALGORITHM
            payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                logger.info(f"Client connected: {sid} (user: {user_id})")
                return True
        except Exception as e:
            logger.warning(f"WebSocket JWT validation failed for {sid}: {e}")

    # Allow connection without token for backward compatibility,
    # but log a warning
    logger.info(f"Client connected: {sid} (unauthenticated)")


@sio.on("join-session")
async def handle_join_session(sid, data):
    from app.core.redis import add_participant, get_participants

    session_id = data.get("sessionId")
    username = data.get("username", "Anonymous")
    container_id = data.get("containerId")

    await sio.enter_room(sid, session_id)

    # Track participant in Redis
    await add_participant(session_id, sid, username)
    participants = await get_participants(session_id)

    # Notify everyone in the room about the new participant
    await sio.emit("participants-update", participants, room=session_id)
    await sio.emit("user-joined-webrtc", sid, room=session_id, skip_sid=sid)

    if container_id:
        async def on_terminal_data(target_sid, output_data):
            await sio.emit("terminal-data", output_data.decode(errors='replace'), to=target_sid)
        await terminal_manager.create_terminal_socket(container_id, sid, on_terminal_data)


@sio.on("terminal-input")
async def handle_terminal_input(sid, data):
    terminal_manager.write_to_terminal(sid, data)


@sio.on("terminal-resize")
async def handle_terminal_resize(sid, data):
    cols = data.get("cols", 80)
    rows = data.get("rows", 24)
    terminal_manager.resize_terminal(sid, cols, rows)


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
    from app.core.redis import remove_participant_globally, get_participants

    logger.info(f"Client disconnected: {sid}")
    terminal_manager.close_terminal(sid)

    # Remove from participants (Redis-backed)
    session_id = await remove_participant_globally(sid)
    if session_id:
        participants = await get_participants(session_id)
        await sio.emit("participants-update", participants, room=session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
