# Colab.ai — API Reference

This document provides a high-level overview of the REST API and WebSocket events available in Colab.ai V2.

## Authentication Endpoints (`/api/auth`)

All secure endpoints require a Bearer token in the `Authorization` header.

- `POST /register`: Register a new user (`username`, `email`, `password`)
- `POST /login`: Authenticate and receive a JWT (`username`, `password`)
- `GET /me`: Get current authenticated user details

## Workspace Sessions (`/api/sessions`)

- `GET /`: List all active sessions the user has access to
- `POST /create`: Create a new session (`osType`, `snapshotId`)
- `GET /{id}`: Get details of a specific session
- `DELETE /{id}`: Terminate a session (Requires Admin/Owner Role)
- `POST /{id}/join`: Join an existing session
- `GET /os-options`: List available OS images

## Container Operations (`/api/containers`)

*Note: Handled transparently by the Orchestrator Interface (Docker/Kubernetes).*

- `POST /`: Provision a new container
- `GET /{id}`: Get container status
- `DELETE /{id}`: Stop and remove a container
- `POST /{id}/exec`: Execute a command
- `POST /{id}/snapshot`: Commit container state to an image
- `GET /{id}/files`: List directory contents
- `GET /{id}/files/read`: Read file contents
- `POST /{id}/files/write`: Write file contents

## Cloudflare Tunnels (`/api/tunnels`)

- `POST /create`: Spawn a new `cloudflared` tunnel (Subject to per-user quotas)
- `GET /`: List all active tunnels
- `GET /health`: Tunnel broker subsystem health check
- `GET /{id}`: Get tunnel info for a session
- `DELETE /{id}`: Terminate a tunnel

## AI Agent (`/api/ai`)

- `GET /providers`: List available AI providers and their models
- `POST /chat`: Send a message to the AI agent (`messages`, `provider`, `model`)

---

## Real-Time WebSocket Events

The Socket.io server handles cross-replica state synchronization via Redis.
Connection requires JWT validation via query string (`?token=...`) or `Authorization` header.

### Client-to-Server Events

- `join-session`: Join a workspace room
- `terminal-input`: Send keystrokes to the pseudo-terminal
- `terminal-resize`: Update terminal dimensions (`cols`, `rows`)
- `editor-change`: Broadcast code editor deltas
- `webrtc-offer` / `webrtc-answer` / `webrtc-ice-candidate`: WebRTC signaling

### Server-to-Client Events

- `participants-update`: Emitted when users join/leave a session
- `terminal-data`: Streamed output from the pseudo-terminal
- `editor-sync`: Received code editor deltas from peers
- `user-joined-webrtc`: Notification for P2P voice/video setup
