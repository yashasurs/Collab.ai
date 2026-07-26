"""
Abstract container orchestrator interface.

Defines the contract that all container backends (Docker, Kubernetes, etc.)
must implement, enabling pluggable orchestration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResourceLimits:
    """Resource constraints for a container/pod."""
    memory_mb: int = 512
    cpu_cores: float = 0.5
    disk_mb: int = 1024


@dataclass
class ContainerInfo:
    """Information about a running container/pod."""
    id: str
    status: str
    image: str
    labels: dict = field(default_factory=dict)


@dataclass
class ExecResult:
    """Result of executing a command in a container."""
    exit_code: int
    output: str


@dataclass
class FileInfo:
    """Information about a file in a container."""
    name: str
    path: str
    is_dir: bool


@dataclass
class SnapshotInfo:
    """Information about a container snapshot."""
    snapshot_id: str
    image_id: str
    name: str


class ContainerOrchestrator(ABC):
    """Abstract base class for container orchestration backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Orchestrator identifier (e.g., 'docker', 'kubernetes')."""
        ...

    @abstractmethod
    async def create(
        self,
        image: str,
        resources: Optional[ResourceLimits] = None,
        labels: Optional[dict] = None,
        snapshot_id: Optional[str] = None,
    ) -> ContainerInfo:
        """Create and start a new container/pod."""
        ...

    @abstractmethod
    async def get(self, container_id: str) -> ContainerInfo:
        """Get information about a running container."""
        ...

    @abstractmethod
    async def remove(self, container_id: str) -> bool:
        """Stop and remove a container."""
        ...

    @abstractmethod
    async def exec(self, container_id: str, command: str) -> ExecResult:
        """Execute a command inside a container."""
        ...

    @abstractmethod
    async def list_files(self, container_id: str, path: str = "/") -> list[FileInfo]:
        """List files in a directory inside the container."""
        ...

    @abstractmethod
    async def read_file(self, container_id: str, path: str) -> str:
        """Read a file from inside the container."""
        ...

    @abstractmethod
    async def write_file(self, container_id: str, path: str, content: str) -> bool:
        """Write content to a file inside the container."""
        ...

    @abstractmethod
    async def snapshot(self, container_id: str, name: str, description: str = "") -> SnapshotInfo:
        """Create a snapshot of the container's current state."""
        ...

    @abstractmethod
    async def setup_edit_command(self, container_id: str) -> bool:
        """Install the 'edit' helper command in the container."""
        ...
