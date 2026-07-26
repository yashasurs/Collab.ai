"""
Docker orchestrator implementation.

Wraps the Docker SDK behind the abstract ContainerOrchestrator interface.
This is the current default for local development and single-host deployment.
"""

import uuid
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import docker
from docker.errors import NotFound, APIError, ImageNotFound

from app.services.orchestrator import (
    ContainerOrchestrator,
    ContainerInfo,
    ExecResult,
    FileInfo,
    SnapshotInfo,
    ResourceLimits,
)

logger = logging.getLogger(__name__)

OS_IMAGE_MAP = {
    "alpine": "colab-alpine:latest",
    "ubuntu": "colab-ubuntu:latest",
    "debian": "colab-debian:latest",
    "fedora": "colab-fedora:latest",
    "arch": "colab-arch:latest",
}
DEFAULT_IMAGE = "alpine:latest"

# Thread pool for blocking Docker SDK calls
_executor = ThreadPoolExecutor(max_workers=10)


class DockerOrchestrator(ContainerOrchestrator):
    """Docker SDK-based container orchestrator."""

    def __init__(self):
        try:
            self._client = docker.from_env()
            logger.info("Docker orchestrator initialized")
        except Exception as e:
            logger.error(f"Docker daemon unavailable: {e}")
            self._client = None

    @property
    def name(self) -> str:
        return "docker"

    def _ensure_client(self):
        """Raise if Docker daemon is not available."""
        if self._client is None:
            raise RuntimeError("Docker daemon is not available")

    async def create(
        self,
        image: str,
        resources: Optional[ResourceLimits] = None,
        labels: Optional[dict] = None,
        snapshot_id: Optional[str] = None,
    ) -> ContainerInfo:
        self._ensure_client()
        resources = resources or ResourceLimits()

        # Resolve image
        if snapshot_id:
            resolved_image = snapshot_id
        else:
            resolved_image = OS_IMAGE_MAP.get(image, image)
            if resolved_image not in OS_IMAGE_MAP.values() and image in OS_IMAGE_MAP:
                resolved_image = OS_IMAGE_MAP[image]

        try:
            container = self._client.containers.run(
                image=resolved_image,
                detach=True,
                tty=True,
                stdin_open=True,
                mem_limit=f"{resources.memory_mb}m",
                cpu_period=100000,
                cpu_quota=int(resources.cpu_cores * 100000),
                network_mode="bridge",
                labels={**(labels or {}), "colab.ai": "workspace"},
            )

            # Install edit command
            await self.setup_edit_command(container.id)

            return ContainerInfo(
                id=container.id,
                status=container.status,
                image=resolved_image,
                labels=container.labels,
            )
        except ImageNotFound:
            raise RuntimeError(f"Image '{resolved_image}' not found. Build the OS images first.")
        except APIError as e:
            raise RuntimeError(f"Docker API error: {e}")

    async def get(self, container_id: str) -> ContainerInfo:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            return ContainerInfo(
                id=container.id,
                status=container.status,
                image=str(container.image.tags),
                labels=container.labels,
            )
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")

    async def remove(self, container_id: str) -> bool:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove()
            return True
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Docker API error: {e}")

    async def exec(self, container_id: str, command: str) -> ExecResult:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            exit_code, output = container.exec_run(
                cmd=["sh", "-c", command],
                stream=False,
                demux=False,
            )
            return ExecResult(
                exit_code=exit_code,
                output=output.decode("utf-8", errors="replace") if output else "",
            )
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Docker API error: {e}")

    async def list_files(self, container_id: str, path: str = "/") -> list[FileInfo]:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            exit_code, output = container.exec_run(f"ls -F {path}")
            if exit_code != 0:
                return []

            lines = output.decode().splitlines()
            files = []
            for line in lines:
                is_dir = line.endswith("/")
                name = line.rstrip("/")
                files.append(FileInfo(
                    name=name,
                    path=f"{path.rstrip('/')}/{name}",
                    is_dir=is_dir,
                ))
            return files
        except Exception as e:
            raise RuntimeError(f"Failed to list files: {e}")

    async def read_file(self, container_id: str, path: str) -> str:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            exit_code, output = container.exec_run(f"cat {path}")
            if exit_code != 0:
                raise RuntimeError(f"File not found or unreadable: {path}")
            return output.decode(errors="replace")
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")

    async def write_file(self, container_id: str, path: str, content: str) -> bool:
        self._ensure_client()
        try:
            container = self._client.containers.get(container_id)
            escaped_content = content.replace("'", "'\\''")
            cmd = f"printf '%s' '{escaped_content}' > {path}"
            exit_code, output = container.exec_run(["sh", "-c", cmd])
            if exit_code != 0:
                raise RuntimeError(f"Failed to write file: {output.decode()}")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to write file: {e}")

    async def snapshot(self, container_id: str, name: str, description: str = "") -> SnapshotInfo:
        self._ensure_client()
        snapshot_id = str(uuid.uuid4())[:8]
        repository = f"colab-snapshot-{snapshot_id}"

        try:
            container = self._client.containers.get(container_id)
            image = container.commit(
                repository=repository,
                tag="latest",
                message=description,
                author="colab.ai",
            )
            return SnapshotInfo(
                snapshot_id=repository,
                image_id=image.id,
                name=name,
            )
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Docker API error: {e}")

    async def setup_edit_command(self, container_id: str) -> bool:
        """Install the 'edit' helper command."""
        try:
            container = self._client.containers.get(container_id)
            script = '#!/bin/sh\nabs_path=$(readlink -f "$1" 2>/dev/null || echo "$1")\nprintf "\\033]0;EDIT:%s\\007" "$abs_path"\n'
            cmd = f"cat << 'EOF' > /usr/bin/edit\n{script}EOF\nchmod +x /usr/bin/edit"
            container.exec_run(["sh", "-c", cmd], user="root")
            return True
        except Exception as e:
            logger.warning(f"Failed to install edit command: {e}")
            return False
