# Build the workspace image
docker build -t colab-alpine:latest -f docker/workspace/Dockerfile docker/workspace

# Run the entire stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild specific service
docker-compose up -d --build backend
