"""
Container management router.

All container operations go through the abstract orchestrator interface,
making the backend agnostic to whether Docker or Kubernetes is in use.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from app.schemas.schemas import CreateContainerRequest, ExecCommandRequest, SnapshotContainerRequest, WriteFileRequest
from app.auth.dependencies import get_current_user
from app.models.models import User
from app.services.orchestrator.factory import orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
async def create_container(req: CreateContainerRequest, current_user: User = Depends(get_current_user)):
    """Create a new container/pod for a workspace session."""
    try:
        info = await orchestrator.create(
            image=req.osType or "alpine",
            snapshot_id=req.snapshotId,
        )
        return {
            "success": True,
            "containerId": info.id,
            "status": info.status,
            "image": info.image,
        }
    except RuntimeError as e:
        status = 404 if "not found" in str(e).lower() else 500
        raise HTTPException(status_code=status, detail=str(e))


@router.get("/{container_id}")
async def get_container(container_id: str, current_user: User = Depends(get_current_user)):
    """Get container information."""
    try:
        info = await orchestrator.get(container_id)
        return {
            "success": True,
            "containerId": info.id,
            "status": info.status,
            "image": info.image,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{container_id}")
async def remove_container(container_id: str, current_user: User = Depends(get_current_user)):
    """Stop and remove a container."""
    try:
        await orchestrator.remove(container_id)
        return {"success": True, "message": f"Container {container_id} stopped and removed"}
    except RuntimeError as e:
        status = 404 if "not found" in str(e).lower() else 500
        raise HTTPException(status_code=status, detail=str(e))


@router.post("/{container_id}/exec")
async def exec_command(container_id: str, req: ExecCommandRequest, current_user: User = Depends(get_current_user)):
    """Execute a command inside a container."""
    try:
        result = await orchestrator.exec(container_id, req.command)
        return {
            "success": result.exit_code == 0,
            "exitCode": result.exit_code,
            "output": result.output,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{container_id}/snapshot")
async def snapshot_container(container_id: str, req: SnapshotContainerRequest, current_user: User = Depends(get_current_user)):
    """Create a snapshot of the container's current state."""
    try:
        info = await orchestrator.snapshot(container_id, req.name, req.description or "")
        return {
            "success": True,
            "snapshotId": info.snapshot_id,
            "imageId": info.image_id,
            "name": info.name,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{container_id}/files")
async def list_files(container_id: str, path: str = "/", current_user: User = Depends(get_current_user)):
    """List files in a directory inside the container."""
    try:
        files = await orchestrator.list_files(container_id, path)
        return {
            "success": True,
            "files": [
                {"name": f.name, "isDir": f.is_dir, "path": f.path}
                for f in files
            ],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{container_id}/files/read")
async def read_file(container_id: str, path: str, current_user: User = Depends(get_current_user)):
    """Read a file from inside the container."""
    try:
        content = await orchestrator.read_file(container_id, path)
        return {"success": True, "content": content}
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{container_id}/files/write")
async def write_file(container_id: str, req: WriteFileRequest, current_user: User = Depends(get_current_user)):
    """Write content to a file inside the container."""
    try:
        await orchestrator.write_file(container_id, req.path, req.content)
        return {"success": True}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
