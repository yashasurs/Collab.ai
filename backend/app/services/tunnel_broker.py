"""
Tunnel broker service.

Manages cloudflared tunnel lifecycle with:
- Per-user quotas
- Idle timeout detection
- Automatic orphan cleanup
- State stored in Redis (not in-memory)
"""

import os
import json
import time
import asyncio
import subprocess
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")

# Configuration
MAX_TUNNELS_PER_USER = int(os.getenv("MAX_TUNNELS_PER_USER", "3"))
TUNNEL_IDLE_TIMEOUT_SECONDS = int(os.getenv("TUNNEL_IDLE_TIMEOUT", "1800"))  # 30 min
TUNNEL_HEALTH_INTERVAL = 60  # Check tunnel health every 60s


@dataclass
class TunnelInfo:
    """Information about an active tunnel."""
    session_id: str
    user_id: str
    url: str
    local_port: int
    created_at: float
    last_active: float
    pid: int  # cloudflared process PID


REDIS_TUNNEL_PREFIX = "tunnel:"
REDIS_USER_TUNNELS_PREFIX = "user_tunnels:"


class TunnelBroker:
    """
    Manages tunnel lifecycle with quotas and cleanup.

    Tunnel state is stored in Redis for cross-replica visibility.
    The actual cloudflared processes run on the local host.
    """

    def __init__(self):
        self._local_processes: dict[str, subprocess.Popen] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the background cleanup task."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Tunnel broker started")

    async def stop(self):
        """Stop the broker and clean up all tunnels."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Terminate all local tunnel processes
        for session_id, proc in list(self._local_processes.items()):
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        self._local_processes.clear()
        logger.info("Tunnel broker stopped, all tunnels closed")

    async def create_tunnel(
        self,
        session_id: str,
        user_id: str,
        local_port: int = 8080,
    ) -> TunnelInfo:
        """Create a new cloudflared tunnel with quota enforcement."""

        # Check if tunnel already exists for this session
        existing = await self._get_tunnel_info(session_id)
        if existing:
            return existing

        # Enforce per-user quota
        user_tunnel_count = await self._get_user_tunnel_count(user_id)
        if user_tunnel_count >= MAX_TUNNELS_PER_USER:
            raise RuntimeError(
                f"Tunnel quota exceeded: maximum {MAX_TUNNELS_PER_USER} "
                f"concurrent tunnels per user (current: {user_tunnel_count})"
            )

        # Start cloudflared process
        local_url = f"http://localhost:{local_port}"
        try:
            proc = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", local_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "cloudflared not found. Install it from "
                "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            )

        # Wait for tunnel URL
        tunnel_url = None
        deadline = time.time() + 10
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            match = TUNNEL_URL_PATTERN.search(line)
            if match:
                tunnel_url = match.group(0)
                break

        if not tunnel_url:
            proc.terminate()
            raise RuntimeError("Timed out waiting for cloudflared tunnel URL")

        # Store process locally and info in Redis
        self._local_processes[session_id] = proc
        now = time.time()

        info = TunnelInfo(
            session_id=session_id,
            user_id=user_id,
            url=tunnel_url,
            local_port=local_port,
            created_at=now,
            last_active=now,
            pid=proc.pid,
        )

        await self._store_tunnel_info(info)
        await self._add_user_tunnel(user_id, session_id)

        logger.info(f"Tunnel created for session {session_id} (user {user_id}): {tunnel_url}")
        return info

    async def close_tunnel(self, session_id: str) -> bool:
        """Close a specific tunnel."""
        info = await self._get_tunnel_info(session_id)

        # Terminate local process
        proc = self._local_processes.pop(session_id, None)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception:
                pass

        # Clean up Redis state
        if info:
            await self._remove_tunnel_info(session_id)
            await self._remove_user_tunnel(info.user_id, session_id)
            logger.info(f"Tunnel closed for session {session_id}")
            return True

        return False

    async def get_tunnel(self, session_id: str) -> Optional[TunnelInfo]:
        """Get tunnel info for a session."""
        return await self._get_tunnel_info(session_id)

    async def list_tunnels(self) -> list[TunnelInfo]:
        """List all active tunnels."""
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            keys = []
            cursor = 0
            while True:
                cursor, batch = await r.scan(cursor, match=f"{REDIS_TUNNEL_PREFIX}*", count=100)
                keys.extend(batch)
                if cursor == 0:
                    break

            tunnels = []
            for key in keys:
                data = await r.get(key)
                if data:
                    d = json.loads(data)
                    tunnels.append(TunnelInfo(**d))
            return tunnels
        except Exception:
            # Fallback: list local processes
            return []

    async def touch(self, session_id: str):
        """Update the last_active timestamp for a tunnel."""
        info = await self._get_tunnel_info(session_id)
        if info:
            info.last_active = time.time()
            await self._store_tunnel_info(info)

    async def health_check(self, session_id: str) -> bool:
        """Check if a tunnel's cloudflared process is still running."""
        proc = self._local_processes.get(session_id)
        if proc is None:
            return False
        return proc.poll() is None  # None means still running

    # ── Redis helpers ─────────────────────────────────────────────────────

    async def _get_tunnel_info(self, session_id: str) -> Optional[TunnelInfo]:
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            data = await r.get(f"{REDIS_TUNNEL_PREFIX}{session_id}")
            if data:
                return TunnelInfo(**json.loads(data))
        except Exception:
            pass
        return None

    async def _store_tunnel_info(self, info: TunnelInfo):
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            data = json.dumps({
                "session_id": info.session_id,
                "user_id": info.user_id,
                "url": info.url,
                "local_port": info.local_port,
                "created_at": info.created_at,
                "last_active": info.last_active,
                "pid": info.pid,
            })
            await r.set(f"{REDIS_TUNNEL_PREFIX}{info.session_id}", data)
        except Exception as e:
            logger.warning(f"Failed to store tunnel info in Redis: {e}")

    async def _remove_tunnel_info(self, session_id: str):
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            await r.delete(f"{REDIS_TUNNEL_PREFIX}{session_id}")
        except Exception:
            pass

    async def _get_user_tunnel_count(self, user_id: str) -> int:
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            count = await r.scard(f"{REDIS_USER_TUNNELS_PREFIX}{user_id}")
            return count or 0
        except Exception:
            return 0

    async def _add_user_tunnel(self, user_id: str, session_id: str):
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            await r.sadd(f"{REDIS_USER_TUNNELS_PREFIX}{user_id}", session_id)
        except Exception:
            pass

    async def _remove_user_tunnel(self, user_id: str, session_id: str):
        try:
            from app.core.redis import get_async_redis
            r = await get_async_redis()
            await r.srem(f"{REDIS_USER_TUNNELS_PREFIX}{user_id}", session_id)
        except Exception:
            pass

    # ── Background cleanup ────────────────────────────────────────────────

    async def _cleanup_loop(self):
        """Periodically check for idle/dead tunnels and clean them up."""
        while self._running:
            try:
                await asyncio.sleep(TUNNEL_HEALTH_INTERVAL)

                for session_id in list(self._local_processes.keys()):
                    # Check if process is still alive
                    if not await self.health_check(session_id):
                        logger.warning(f"Tunnel process died for session {session_id}, cleaning up")
                        await self.close_tunnel(session_id)
                        continue

                    # Check idle timeout
                    info = await self._get_tunnel_info(session_id)
                    if info and (time.time() - info.last_active) > TUNNEL_IDLE_TIMEOUT_SECONDS:
                        logger.info(f"Tunnel idle timeout for session {session_id}")
                        await self.close_tunnel(session_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tunnel cleanup error: {e}")


# Singleton
tunnel_broker = TunnelBroker()
