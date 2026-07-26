"""
Redis connection manager.

Provides a centralized Redis client for:
- Socket.io cross-replica event fan-out
- Session participant state
- Tunnel lifecycle state
- Ephemeral caching
"""

import os
import json
import logging
from typing import Optional, Any

import redis.asyncio as aioredis
import redis as sync_redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ---------------------------------------------------------------------------
# Async Redis client (for use in async route handlers and Socket.io)
# ---------------------------------------------------------------------------

_async_pool: Optional[aioredis.Redis] = None


async def get_async_redis() -> aioredis.Redis:
    """Get or create the async Redis connection pool."""
    global _async_pool
    if _async_pool is None:
        _async_pool = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=50,
        )
    return _async_pool


async def close_async_redis():
    """Close the async Redis connection pool."""
    global _async_pool
    if _async_pool is not None:
        await _async_pool.close()
        _async_pool = None
        logger.info("Async Redis connection closed")


# ---------------------------------------------------------------------------
# Sync Redis client (for Socket.io manager initialization)
# ---------------------------------------------------------------------------

def get_sync_redis() -> sync_redis.Redis:
    """Create a synchronous Redis client (used by Socket.io Redis adapter)."""
    return sync_redis.from_url(REDIS_URL, decode_responses=True)


# ---------------------------------------------------------------------------
# Session participant helpers (Redis-backed)
# ---------------------------------------------------------------------------

PARTICIPANTS_KEY_PREFIX = "session:participants:"


async def add_participant(session_id: str, sid: str, username: str):
    """Add a participant to a session's participant list in Redis."""
    r = await get_async_redis()
    participant = json.dumps({"sid": sid, "username": username})
    await r.hset(f"{PARTICIPANTS_KEY_PREFIX}{session_id}", sid, participant)


async def remove_participant(session_id: str, sid: str):
    """Remove a participant from a session in Redis."""
    r = await get_async_redis()
    await r.hdel(f"{PARTICIPANTS_KEY_PREFIX}{session_id}", sid)


async def get_participants(session_id: str) -> list[dict]:
    """Get all participants for a session from Redis."""
    r = await get_async_redis()
    raw = await r.hgetall(f"{PARTICIPANTS_KEY_PREFIX}{session_id}")
    return [json.loads(v) for v in raw.values()]


async def find_participant_session(sid: str) -> Optional[str]:
    """Find which session a participant belongs to (by scanning)."""
    r = await get_async_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=f"{PARTICIPANTS_KEY_PREFIX}*", count=100)
        for key in keys:
            if await r.hexists(key, sid):
                return key.replace(PARTICIPANTS_KEY_PREFIX, "")
        if cursor == 0:
            break
    return None


async def remove_participant_globally(sid: str) -> Optional[str]:
    """Remove a participant from any session they belong to. Returns session_id or None."""
    session_id = await find_participant_session(sid)
    if session_id:
        await remove_participant(session_id, sid)
    return session_id


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def redis_health_check() -> bool:
    """Check if Redis is reachable."""
    try:
        r = await get_async_redis()
        return await r.ping()
    except Exception:
        return False
