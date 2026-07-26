# Colab.ai Project Documentation

## 1. Project Overview

**Colab.ai** is an open-source platform providing real-time collaborative workspaces with persistent Linux environments. It is designed for developers to share a common Linux workspace in order to collaborate seamlessly on code, troubleshoot issues, pair program, and conduct live technical reviews.

The platform allows developers to quickly provision lightweight Docker containers running various Linux distributions (Alpine, Ubuntu, Debian, Fedora, Arch) and share terminal access, code editing, and video communications directly through the browser.

---

## 2. Implementation Details

### Architecture & Tech Stack
The project follows a standard monolithic backend with a decoupled single-page application frontend.

* **Frontend (React 18 & TypeScript):**
  * **Code Editor:** Integrates **Monaco Editor** (the engine behind VS Code) for a rich, in-browser coding experience.
  * **Terminal Emulator:** Uses **xterm.js** to provide a fully functional terminal interface directly in the browser.
  * **Video Communication:** Leverages **WebRTC** to enable real-time video and audio calls between collaborators in the same session.
  * **Real-time Sync:** Uses **Socket.io-client** to synchronize terminal I/O, file changes, and collaborative actions with the backend.

* **Backend (Python 3.11 & FastAPI):**
  * **REST API & WebSockets:** Built on **FastAPI** and `python-socketio`, the backend efficiently handles standard HTTP requests (auth, tunnel creation, session management) alongside real-time WebSocket streams for terminal multiplexing.
  * **Container Management:** Uses the **Python Docker SDK** to dynamically provision, manage, and isolate Linux containers for each user session.
  * **Secure Tunneling:** Integrates with **cloudflared** to dynamically expose local container ports to public `trycloudflare.com` URLs. This enables users to share their local sessions over the internet securely without complex network configuration.
  * **Authentication:** Implements **JWT-based authentication** with SQLite and SQLAlchemy to handle user registration and login securely.
  * **AI Assistant:** Features an AI coding assistant powered by the **Gemini API** (`gemini-1.5-pro`). It assists users with programming questions, debugging, and shell commands.
  * **Snapshots (State Persistence):** Allows users to save the current state of their workspace container as a new Docker image using Docker's commit functionality. This enables pausing and resuming environments seamlessly.

### Code Organization
* `backend/app/routers/`: Modularized API endpoints separating concerns into `auth.py`, `containers.py`, `sessions.py`, `snapshots.py`, `tunnels.py`, and `ai_agent.py`.
* `frontend/src/`: Component-driven structure with distinct `pages/` (Dashboard, Workspace, Login, etc.) and reusable `components/`.
* `docker/`: Contains customized Dockerfiles for the different Linux OS environments provided to users.

---

## 3. What is Yet to be Implemented (Roadmap)

Based on the current state of the codebase, the following features and improvements are either missing, partially implemented, or planned for the future:

1. **Advanced Role-Based Access Control (RBAC):**
   * While basic JWT authentication exists, the system lacks advanced team and role management (e.g., distinguishing permissions between a Team Lead, a Core Developer, and an External Contributor).

2. **Multi-Container Sessions:**
   * Currently, a single session maps directly to a single Docker container. Supporting multi-container networks (e.g., integrating `docker-compose` equivalents within a single session) would allow for more complex, multi-tier project environments.

3. **Robust Container Lifecycle Management:**
   * **Automatic Cleanup:** There is a need for background tasks to automatically detect and clean up dormant containers and orphaned cloudflared tunnels to prevent resource leaks.
   * **Resource Quotas:** While mentioned in the architecture design, strict enforcement of CPU and memory limits per container needs robust implementation to prevent abuse in a multi-tenant setup.

4. **Persistent Cloud Storage Integration:**
   * Workspace state is currently saved via Docker Snapshots (committing the container to an image). Abstracting user files to persistent volumes or cloud storage (e.g., AWS S3 or EFS) independent of the container image would provide more efficient and reliable long-term file persistence.

5. **Comprehensive Test Suite:**
   * The project currently relies on basic interactive/socketio tests. A comprehensive suite of unit, integration, and end-to-end tests covering both frontend components and backend routers is necessary for production readiness.

6. **End-to-End WebSocket Security:**
   * Ensuring that WebSocket channels are fully secured by mapping active JWT tokens prior to establishing the connection and broadcasting terminal I/O, preventing unauthorized access to active sessions.

7. **CI/CD Pipelines:**
   * Implementing automated pipelines (e.g., GitHub Actions) for linting, testing, Docker image building, and deployment is needed to streamline the development workflow.

8. **AI Assistant Enhancement (MCP Integration):**
   * Integrating a Model Context Protocol (MCP) with a fine-tuned model. This will enhance the AI assistant by providing deeper context awareness and more specialized developer assistance directly within the shared workspace.
