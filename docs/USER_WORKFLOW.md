# User Workflow Details

This document provides a step-by-step description of how a user interacts with the Colab.ai platform.

## 1. Onboarding & Authentication
**Route:** `frontend/src/pages/Landing.tsx` -> `/register` | `/login`

1. **Landing Page:** A user lands on the monochrome, professional homepage (Colab.ai). They can read about the features: AI Pair Programming, Instant OS Labs, Secure Networking, Real-Time Multiplayer, and Stateful Snapshots.
2. **Registration:** They click "Start Building Now" or "Get Started", redirecting them to `/register`. They enter a Username, Email, and Password. The backend securely checks for duplicates and stores a `bcrypt`ed hash of the password.
3. **Login:** They are redirected to `/login`. Upon authenticating with their credentials, an `OAuth2PasswordRequestForm` gives them an `access_token` (JWT). This is saved in `localStorage` securely by the frontend.

## 2. The Dashboard
**Route:** `frontend/src/pages/Dashboard.tsx`

1. **Viewing Sessions:** After login, the user lands on `/dashboard`. They see a count of their Active Sessions and a list of Recent Sessions represented as individual cards showing details like the OS icon, the participants (up to 3 icons), and the session UUID.
2. **Creating a New Session:** They click the large "Create New Session" button. This triggers a modal (`LabSelector.tsx`) that dims the rest of the application.

## 3. Launching a Workspace
**Component:** `LabSelector.tsx`

1. **Environment Selection:** The user is presented with a grid of OS options:
    - **Standard OS Images:** Alpine (Default), Ubuntu 22.04, Debian 12, Fedora 39, Arch Linux.
    - **Your Snapshots:** A list of previously saved workspace states (if any exist).
2. **Launch:** Selecting one (e.g., Ubuntu) highlights it. The user clicks "Launch Ubuntu" at the bottom.
3. **Boot Sequence:** 
    - The frontend sends a `POST /sessions/create` request.
    - The backend interacts with the Docker daemon to boot an isolated Linux container with the requested image.
    - The container ID is linked to the newly minted Session in the SQLite database.
4. **Transition:** The user is routed to `/workspace/${sessionId}`.

## 4. The Collaborative Workspace IDE
**Route:** `frontend/src/pages/Workspace.tsx`

When the workspace loads, the following components initialize simultaneously:
1. **WebSocket Connection (`main.py`):** The client emits a `join-session` event over Socket.io, which connects the user to the Session's specific room.
2. **Code Editor (`Editor.tsx`):** The Monaco Editor (VS Code engine in the browser) loads. As the user or any collaborator types, changes are emitted in real-time to the server and synchronized with latency-free UI.
3. **Terminal (`Terminal.tsx`):** A bash terminal appears using `xterm.js`. Because the user booted an Ubuntu container, they have full root/ghostuser access. They can install packages (`apt-get install htop`), run scripts (`python app.py`), or start servers. This is entirely synced across all participants.
4. **Networking (`tunnels.py`):** In the background, `cloudflared` launches an ephemeral tunnel (e.g., `https://rapid-rabbit-123.trycloudflare.com`). Any server running in the terminal on port 8000 is accessible globally from this URL.
5. **Video Call (`VideoCall.tsx`):** WebRTC starts. The user is prompted for webcam/microphone permissions. Once approved, they see their own face in the bottom left, and peer-to-peer connections are negotiated instantly for any other existing collaborators in the room.

## 5. Saving State & Exiting
**Route:** `Workspace.tsx Header` -> `snapshots.py`

1. **Snapshot Creation:** If the user has heavily customized their OS (installed `npm`, set up a custom Postgres database inside the container, wrote complex files), they click "**Save Snapshot**" in the top navigation bar.
2. **Prompt:** A native prompt asks for a snapshot name: `"Snapshot ${Date}"`.
3. **Commit Pipeline:** The backend freezes the current state of the running Docker container and commits it into a localized image tagging it with a timestamp/UUID.
4. **Exit:** The user clicks "Exit" to return to the `/dashboard`. The session remains alive until the container exits or is manually killed by the backend, meaning collaborators can continue working uninterrupted.