# Features Implementation Details

This document provides an in-depth look at how each core feature of Colab.ai is implemented on both the frontend and backend.

## 1. Instant OS Labs (Container Management)
**Goal:** Provide users with isolated, fast-booting Linux environments.

**Backend Implementation (`backend/app/routers/containers.py`):**
- Utilizes the `docker` Python SDK to interact with the host's Docker daemon.
- When a user requests a session with a specific OS (Alpine, Ubuntu, Debian, Fedora, Arch), the backend maps the OS choice to a pre-built Docker image (defined in `docker/os-images/`).
- The container is spun up with specific constraints: `mem_limit="512m"` and `cpu_quota=50000` (equivalent to 0.5 CPU) to ensure resource isolation.
- File browsing and reading/writing are implemented by executing `sh` commands (`ls -F`, `cat`, `printf`) inside the running container using `container.exec_run()`.

**Frontend Implementation:**
- Users select an OS from the `LabSelector.tsx` component.
- The `FileBrowser.tsx` component fetches the container's contents recursively.

## 2. Secure Networking (Cloudflared Tunnels)
**Goal:** Allow users to share their workspace publicly and securely without opening firewall ports.

**Backend Implementation (`backend/app/routers/tunnels.py`):**
- Utilizes the `cloudflared` CLI.
- When a tunnel is requested, a subprocess is launched: `cloudflared tunnel --url http://localhost:8080`.
- The backend reads the subprocess standard output to extract the ephemeral `https://*.trycloudflare.com` URL.
- The spawned process is kept alive in memory and explicitly terminated when the session is closed.

**Frontend Implementation:**
- The tunnel URL is typically copied and shared by the user to allow external collaborators to reverse-proxy into the container's exposed services (e.g., a dev server the user runs inside the terminal).

## 3. Real-Time Multiplayer Collaboration
**Goal:** Keep code, terminal inputs, and connected participants completely in sync for all users in a session.

**Backend Implementation (`backend/app/main.py` & `backend/app/core/terminal_manager.py`):**
- **Socket.io** is used for real-time WebSocket communication.
- **Terminal Sync:** `terminal_manager.py` creates a raw socket connection to the Docker container's TTY shell using `docker.api.exec_create()`. Output from this raw socket is broadcasted via an asyncio event loop to all users in the room. Keystrokes sent from the frontend are written back to the Docker socket.
- **Code Sync:** When an `editor-change` event is received, the server broadcasts an `editor-sync` event to everyone else in the `session_id` room.

**Frontend Implementation:**
- `Terminal.tsx` uses `xterm.js` to render the ANSI terminal stream.
- `Editor.tsx` uses `@monaco-editor/react` (the VS Code engine) and hooks into its `onChange` event to emit socket updates. To prevent echo loops, a flag (`isRemoteChange`) ignores incoming socket events so they don't trigger outgoing socket events.

## 4. WebRTC Video/Audio Calling
**Goal:** Enable face-to-face communication inside the IDE.

**Backend Implementation (`backend/app/main.py`):**
- The backend serves entirely as a signaling server for WebRTC.
- It relays `webrtc-offer`, `webrtc-answer`, and `webrtc-ice-candidate` events directly to specific target socket IDs.

**Frontend Implementation (`frontend/src/components/VideoCall.tsx`):**
- Uses the browser's `navigator.mediaDevices.getUserMedia` to capture local audio/video.
- Instantiates `RTCPeerConnection` for each peer in the room. Google's public STUN servers are used for NAT traversal.
- Manages an array of remote streams dynamically as users join or leave the Session.

## 5. Stateful Snapshots
**Goal:** Save environment state dynamically so it can be resumed later.

**Backend Implementation (`backend/app/routers/snapshots.py`):**
- Given an active session and container ID, the server calls the Docker API to `commit()` the container into a brand new image tagged with `colab-snapshot-<uuid>`.
- A database record is saved tying the user/session to the saved Docker image name.
- Next time a user creates a session, if a `snapshotId` is provided, that specific custom-built image is booted rather than a base OS image.

## 6. AI Pair Programming
**Goal:** Provide intelligent contextual coding help.

**Backend Implementation (`backend/app/routers/ai_agent.py`):**
- Connects to Google's Gemini API (`generativelanguage.googleapis.com`).
- Accepts a conversation history and safely formats it into the Gemini format.
- A system prompt guides the AI to behave as a concise coding assistant.