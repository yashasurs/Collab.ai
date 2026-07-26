"""
Kubernetes orchestrator implementation (stub).

Provides a Kubernetes Pod-based orchestrator for production deployments.
Each user session becomes a Pod scheduled across a node pool.

NOTE: This is a structural implementation that requires a running K8s cluster.
For local development, use the Docker orchestrator.
"""

import uuid
import logging
from typing import Optional

from app.services.orchestrator import (
    ContainerOrchestrator,
    ContainerInfo,
    ExecResult,
    FileInfo,
    SnapshotInfo,
    ResourceLimits,
)

logger = logging.getLogger(__name__)

# Image map for Kubernetes (could use a private registry)
K8S_IMAGE_MAP = {
    "alpine": "colab-alpine:latest",
    "ubuntu": "colab-ubuntu:latest",
    "debian": "colab-debian:latest",
    "fedora": "colab-fedora:latest",
    "arch": "colab-arch:latest",
}

NAMESPACE = "colab-workspaces"


class KubernetesOrchestrator(ContainerOrchestrator):
    """
    Kubernetes-based container orchestrator.

    Each user session becomes a Pod with:
    - Resource limits (CPU, memory) via LimitRange
    - Persistent storage via PVC
    - Network isolation via NetworkPolicy
    - gVisor/Kata runtime class for security (if configured)
    """

    def __init__(self):
        self._available = False
        try:
            # Attempt to load kubeconfig
            from kubernetes import client, config
            try:
                config.load_incluster_config()  # Running inside K8s
            except config.ConfigException:
                config.load_kube_config()  # Running outside K8s

            self._core_v1 = client.CoreV1Api()
            self._available = True
            logger.info("Kubernetes orchestrator initialized")
        except ImportError:
            logger.warning("kubernetes package not installed — K8s orchestrator unavailable")
        except Exception as e:
            logger.warning(f"Kubernetes not available: {e}")

    @property
    def name(self) -> str:
        return "kubernetes"

    def _ensure_available(self):
        if not self._available:
            raise RuntimeError(
                "Kubernetes is not configured. Install the 'kubernetes' package "
                "and ensure kubeconfig is available."
            )

    async def create(
        self,
        image: str,
        resources: Optional[ResourceLimits] = None,
        labels: Optional[dict] = None,
        snapshot_id: Optional[str] = None,
    ) -> ContainerInfo:
        self._ensure_available()
        from kubernetes import client

        resources = resources or ResourceLimits()
        pod_name = f"colab-session-{uuid.uuid4().hex[:8]}"

        resolved_image = snapshot_id if snapshot_id else K8S_IMAGE_MAP.get(image, image)

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pod_name,
                namespace=NAMESPACE,
                labels={**(labels or {}), "app": "colab-workspace"},
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="workspace",
                        image=resolved_image,
                        stdin=True,
                        tty=True,
                        resources=client.V1ResourceRequirements(
                            limits={
                                "memory": f"{resources.memory_mb}Mi",
                                "cpu": str(resources.cpu_cores),
                            },
                            requests={
                                "memory": f"{resources.memory_mb // 2}Mi",
                                "cpu": str(resources.cpu_cores / 2),
                            },
                        ),
                    )
                ],
                restart_policy="Never",
            ),
        )

        self._core_v1.create_namespaced_pod(namespace=NAMESPACE, body=pod)

        return ContainerInfo(
            id=pod_name,
            status="Pending",
            image=resolved_image,
            labels=labels or {},
        )

    async def get(self, container_id: str) -> ContainerInfo:
        self._ensure_available()
        try:
            pod = self._core_v1.read_namespaced_pod(name=container_id, namespace=NAMESPACE)
            return ContainerInfo(
                id=pod.metadata.name,
                status=pod.status.phase,
                image=pod.spec.containers[0].image,
                labels=pod.metadata.labels or {},
            )
        except Exception as e:
            raise RuntimeError(f"Pod {container_id} not found: {e}")

    async def remove(self, container_id: str) -> bool:
        self._ensure_available()
        try:
            self._core_v1.delete_namespaced_pod(name=container_id, namespace=NAMESPACE)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete pod: {e}")

    async def exec(self, container_id: str, command: str) -> ExecResult:
        self._ensure_available()
        from kubernetes.stream import stream

        try:
            resp = stream(
                self._core_v1.connect_get_namespaced_pod_exec,
                container_id,
                NAMESPACE,
                command=["sh", "-c", command],
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
            return ExecResult(exit_code=0, output=resp)
        except Exception as e:
            return ExecResult(exit_code=1, output=str(e))

    async def list_files(self, container_id: str, path: str = "/") -> list[FileInfo]:
        result = await self.exec(container_id, f"ls -F {path}")
        if result.exit_code != 0:
            return []

        files = []
        for line in result.output.splitlines():
            is_dir = line.endswith("/")
            name = line.rstrip("/")
            files.append(FileInfo(name=name, path=f"{path.rstrip('/')}/{name}", is_dir=is_dir))
        return files

    async def read_file(self, container_id: str, path: str) -> str:
        result = await self.exec(container_id, f"cat {path}")
        if result.exit_code != 0:
            raise RuntimeError(f"File not found: {path}")
        return result.output

    async def write_file(self, container_id: str, path: str, content: str) -> bool:
        escaped = content.replace("'", "'\\''")
        result = await self.exec(container_id, f"printf '%s' '{escaped}' > {path}")
        return result.exit_code == 0

    async def snapshot(self, container_id: str, name: str, description: str = "") -> SnapshotInfo:
        # K8s snapshots work differently — snapshot the PVC, not the container
        raise NotImplementedError(
            "Kubernetes snapshots use PVC snapshots. "
            "This requires a CSI driver with VolumeSnapshot support."
        )

    async def setup_edit_command(self, container_id: str) -> bool:
        script = '#!/bin/sh\nabs_path=$(readlink -f "$1" 2>/dev/null || echo "$1")\nprintf "\\033]0;EDIT:%s\\007" "$abs_path"\n'
        result = await self.exec(
            container_id,
            f"cat << 'EOF' > /usr/bin/edit\n{script}EOF\nchmod +x /usr/bin/edit"
        )
        return result.exit_code == 0
