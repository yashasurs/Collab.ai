# 🚀 Colab.ai

Colab.ai is an open-source platform that provides real-time collaborative workspaces with persistent Linux environments, designed to help students learn programming and collaboration skills.

### ✨ Features

- **🖥️ Persistent Linux Labs**: Lightweight Docker containers with multiple OS options (Alpine, Ubuntu, Debian, Fedora, Arch)
- **🤝 Real-time Collaboration**: Share and access workspaces together via WebSocket
- **🌐 Secure Tunnel Access**: Automatic cloudflared tunnel creation for each session
- **🎥 Video Communication**: Built-in WebRTC video/audio calls
- **💻 Code Editor**: Monaco Editor integration (VS Code editor)
- **🖥️ Terminal Access**: Full terminal access via xterm.js
- **💾 Snapshots**: Save and restore workspace states
- **🤖 AI Assistant**: Coding help powered by AI (OpenAI integration ready)

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend    │
│   (React)   │     │  (FastAPI)   │
└─────────────┘     └──────────────┘
                           │
                           ├──────────▶ Docker Containers
                           │            (Linux Labs)
                           │
                           └──────────▶ Cloudflared Tunnels
                                        (Public Access)
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yashasurs/Colab.ai.git
   cd Colab.ai
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Manual Setup (Development)

If you prefer to run services individually:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
Colab.ai/
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   └── hooks/          # Custom hooks
│   └── package.json
├── backend/                 # FastAPI monolithic backend
│   ├── main.py              # Entry point & Socket.io
│   ├── routers/             # API routes (sessions, ai, containers, tunnels)
│   └── requirements.txt
├── docker/
│   ├── os-images/          # Multiple OS Dockerfiles
│   └── workspace/          # Default Alpine workspace
├── docs/                    # Documentation files
│   ├── ARCHITECTURE.md     # Architecture documentation
│   ├── CLOUDFLARED_IMPLEMENTATION.md
└── docker-compose.yml
```

## 🎯 Use Cases

- **Programming Education**: Teachers create sessions, students join via tunnel URL
- **Team Collaboration**: Developers pair program in real-time with OS choice
- **Code Reviews**: Review code together with live discussions
- **Workshops**: Conduct hands-on programming workshops with persistent environments
- **Interview Practice**: Technical interview preparation with snapshot save/resume

## 🛠️ Technology Stack

### Frontend
- React 18
- TypeScript
- Socket.io-client
- xterm.js (terminal)
- Monaco Editor (code editor)
- WebRTC (video/audio)

### Backend
- Python 3.11
- FastAPI
- python-socketio
- Docker SDK for Python
- SQLite (planned)

### Infrastructure
- Docker (containerization)
- Multiple Linux distributions (Alpine, Ubuntu, Debian, Fedora, Arch)
- cloudflared (secure tunneling)


## 📝 License

This project is licensed under the Apache License Version 2.0 - see the [LICENSE](LICENSE) file for details.


