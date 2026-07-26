"""
Orchestrator factory.

Selects the appropriate container orchestrator based on the
ORCHESTRATOR_TYPE environment variable.
"""

import os
import logging

from app.services.orchestrator import ContainerOrchestrator
from app.services.orchestrator.docker_orchestrator import DockerOrchestrator

logger = logging.getLogger(__name__)


def create_orchestrator() -> ContainerOrchestrator:
    """
    Create and return the appropriate orchestrator instance.

    Controlled by ORCHESTRATOR_TYPE env var:
    - "docker" (default): Direct Docker daemon via Python SDK
    - "kubernetes": Kubernetes Pod-based orchestration
    """
    orchestrator_type = os.getenv("ORCHESTRATOR_TYPE", "docker").lower()

    if orchestrator_type == "kubernetes":
        try:
            from app.services.orchestrator.kubernetes_orchestrator import KubernetesOrchestrator
            orch = KubernetesOrchestrator()
            logger.info("Using Kubernetes orchestrator")
            return orch
        except Exception as e:
            logger.warning(f"Kubernetes orchestrator failed to initialize ({e}), falling back to Docker")

    orch = DockerOrchestrator()
    logger.info("Using Docker orchestrator")
    return orch


# Singleton orchestrator instance
orchestrator = create_orchestrator()
