# Colab.ai 🚀

Colab.ai is a collaborative Linux lab platform designed for modern development teams, educators, and hackers. It provides instant, isolated, browser-based Linux environments with real-time multi-user collaboration, pseudo-terminals, code editing, and integrated AI assistance.

## ✨ Features (V2 Architecture)

- **Instant Linux Workspaces:** Spawn isolated Ubuntu, Alpine, Debian, Fedora, or Arch Linux containers in seconds.
- **Real-Time Collaboration:** Multi-user terminal multiplexing and code editor synchronization, powered by Socket.io and Redis.
- **Integrated AI Assistants:** Chat with Google Gemini, OpenAI, or local LLMs directly in your workspace. Features automatic provider failover.
- **Cloudflare Tunnels:** Instantly expose your local workspace ports to the public internet for testing webhooks and sharing previews.
- **Enterprise RBAC:** Organization → Team → Role → Permission hierarchy for fine-grained access control.
- **Pluggable Orchestration:** Run locally via Docker SDK or deploy to production on Kubernetes.

## 📖 Documentation

- [Architecture Overview](./docs/ARCHITECTURE_V2.md)
- [Performance Benchmarks](./docs/BENCHMARKS.md)
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)
- [API Reference](./docs/API_REFERENCE.md)

## 🚀 Quick Start (Local Development)

1. **Clone & Configure**
   ```bash
   cp backend/.env.example backend/.env
   # Add your API keys to the .env file
   ```

2. **Start Infrastructure**
   ```bash
   docker-compose up -d
   ```

3. **Start Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:socket_app --reload
   ```

4. **Start Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🏗️ Technology Stack

**Backend:** FastAPI, Socket.io, SQLAlchemy (PostgreSQL), Alembic, Redis (Pub/Sub + State)
**Frontend:** React, TypeScript, Vite, TailwindCSS, Xterm.js, Monaco Editor
**Infrastructure:** Docker, Kubernetes, Cloudflare Tunnels
