# Colab.ai — Deployment Guide

This guide covers how to deploy Colab.ai V2 in both local development and production Kubernetes environments.

## Local Development (Docker Compose)

The easiest way to run the full stack locally is using Docker Compose. This utilizes the `DockerOrchestrator` for spawning workspace containers on your local Docker daemon.

### Prerequisites
- Docker Engine & Docker Compose
- Node.js 18+
- Python 3.11+
- API Keys for AI Providers (Gemini or OpenAI)

### Steps

1. **Environment Setup**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY / OPENAI_API_KEY
   ```

2. **Start Infrastructure (PostgreSQL & Redis)**
   ```bash
   cd ..
   docker-compose up -d
   ```

3. **Run Database Migrations**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ```

4. **Start Backend Server**
   ```bash
   uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Start Frontend Dev Server**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Production Deployment (Kubernetes)

For production, Colab.ai utilizes the `KubernetesOrchestrator`. Each user session is spawned as an isolated K8s Pod.

### Prerequisites
- A Kubernetes cluster (EKS, GKE, AKS)
- Ingress Controller (e.g., NGINX Ingress)
- Helm (for deploying dependencies like PostgreSQL/Redis)

### Architecture Configuration

1. **Set the Orchestrator Variable**
   The backend must be configured to use Kubernetes:
   ```env
   ORCHESTRATOR_TYPE=kubernetes
   ```

2. **Backend StatefulSets vs Deployments**
   The FastAPI backend is entirely stateless thanks to Redis. You can deploy it using a standard Kubernetes `Deployment` with a HorizontalPodAutoscaler (HPA).

3. **RBAC Permissions**
   The backend Pods need permissions to spawn workspace Pods. Apply the following `Role` and `RoleBinding`:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     namespace: colab-workspaces
     name: colab-backend-role
   rules:
   - apiGroups: [""]
     resources: ["pods", "pods/exec", "pods/log"]
     verbs: ["get", "list", "watch", "create", "delete"]
   ```

4. **Resource Limits & Security**
   - Workspace Pods enforce memory and CPU limits defined in `KubernetesOrchestrator`.
   - It is highly recommended to configure a `RuntimeClass` like **gVisor** or **Kata Containers** for strong tenant isolation.
   - Configure a `NetworkPolicy` to prevent workspace Pods from accessing the internal cluster network.

### Structured Logging
In production, ensure `LOG_FORMAT=json` is set. This formats all FastAPI logs as JSON, making them ready for ingestion by Fluentd, Promtail, or Datadog agents.
