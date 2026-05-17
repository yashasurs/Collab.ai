# Colab.ai Backend

FastAPI monolithic backend for Colab.ai.

## Features

- **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.11+.
- **Socket.io**: Real-time communication for terminal and code synchronization.
- **Docker SDK**: Manage Linux lab containers directly from the backend.
- **Integrated Services**: AI Agent, Container Management, and Tunnel Management are all part of this monolith.

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

The backend uses environment variables. Create a `.env` file from `.env.example`:

```bash
PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Development

Run the server with Uvicorn:

```bash
uvicorn app.main:socket_app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Check the interactive API docs at `http://localhost:8000/docs`.

## Port Mapping

The backend is configured to run on port **8000**.
This is consistent across the `Dockerfile`, `docker-compose.yml`, and frontend configuration.
