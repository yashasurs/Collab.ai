from fastapi import APIRouter, HTTPException, BackgroundTasks
import docker
import uuid
import logging

from app.schemas.schemas import CreateContainerRequest, ExecCommandRequest, SnapshotContainerRequest

router = APIRouter()
logger = logging.getLogger(__name__)

OS_IMAGE_MAP = {
    "alpine": "colab-alpine:latest",
    "ubuntu": "colab-ubuntu:latest",
    "debian": "colab-debian:latest",
    "fedora": "colab-fedora:latest",
    "arch":   "colab-arch:latest",
}
DEFAULT_IMAGE = "alpine:latest"


def _get_docker():
    try:
        return docker.from_env()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Docker daemon unavailable: {e}")


@router.post("/")
async def create_container(req: CreateContainerRequest):
    client = _get_docker()
    image = OS_IMAGE_MAP.get(req.osType or "alpine", DEFAULT_IMAGE)

    # If creating from snapshot, use snapshot image directly
    if req.snapshotId:
        image = req.snapshotId

    try:
        container = client.containers.run(
            image=image,
            detach=True,
            tty=True,
            stdin_open=True,
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=50000,   # 0.5 CPU
            network_mode="bridge",
            labels={"colab.ai": "workspace"},
        )
        return {
            "success": True,
            "containerId": container.id,
            "status": container.status,
            "image": image,
        }
    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image '{image}' not found. Build the OS images first.")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")


@router.get("/{container_id}")
async def get_container(container_id: str):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        return {
            "success": True,
            "containerId": container.id,
            "status": container.status,
            "image": container.image.tags,
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")


@router.delete("/{container_id}")
async def remove_container(container_id: str):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()
        return {"success": True, "message": f"Container {container_id} stopped and removed"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")


@router.post("/{container_id}/exec")
async def exec_command(container_id: str, req: ExecCommandRequest):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        exit_code, output = container.exec_run(
            cmd=["sh", "-c", req.command],
            stream=False,
            demux=False,
        )
        return {
            "success": exit_code == 0,
            "exitCode": exit_code,
            "output": output.decode("utf-8", errors="replace") if output else "",
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")


@router.post("/{container_id}/snapshot")
async def snapshot_container(container_id: str, req: SnapshotContainerRequest):
    client = _get_docker()
    snapshot_id = str(uuid.uuid4())[:8]
    repository = f"colab-snapshot-{snapshot_id}"

    try:
        container = client.containers.get(container_id)
        image = container.commit(
            repository=repository,
            tag="latest",
            message=req.description or "",
            author="colab.ai",
        )
        return {
            "success": True,
            "snapshotId": repository,
            "imageId": image.id,
            "name": req.name,
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")


@router.get("/{container_id}/files")
async def list_files(container_id: str, path: str = "/"):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        # Simple ls -F to distinguish directories
        exit_code, output = container.exec_run(f"ls -F {path}")
        if exit_code != 0:
            return {"success": False, "files": []}
        
        lines = output.decode().splitlines()
        files = []
        for line in lines:
            is_dir = line.endswith("/")
            name = line.rstrip("/")
            files.append({"name": name, "isDir": is_dir, "path": f"{path.rstrip('/')}/{name}"})
            
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{container_id}/files/read")
async def read_file(container_id: str, path: str):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        exit_code, output = container.exec_run(f"cat {path}")
        if exit_code != 0:
            raise HTTPException(status_code=404, detail="File not found or unreadable")
        return {"success": True, "content": output.decode(errors='replace')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{container_id}/files/write")
async def write_file(container_id: str, path: str, content: str):
    client = _get_docker()
    try:
        container = client.containers.get(container_id)
        # Use a temporary file to write content and then move it to avoid shell escaping issues with large content
        # For simplicity here, we use a basic echo redirection, but in production we'd use put_archive
        escaped_content = content.replace("'", "'\\''")
        cmd = f"printf '%s' '{escaped_content}' > {path}"
        exit_code, output = container.exec_run(["sh", "-c", cmd])
        if exit_code != 0:
             raise HTTPException(status_code=500, detail=f"Failed to write file: {output.decode()}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
