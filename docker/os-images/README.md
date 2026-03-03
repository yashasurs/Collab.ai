# Ghost Labs OS Images

This directory contains Dockerfiles for different Linux distributions that users can choose from when creating a workspace.

## Available OS Options

- **Alpine** (Default) - Lightweight, ~5MB base
- **Ubuntu** - Popular, beginner-friendly, ~80MB base
- **Debian** - Stable, reliable, ~120MB base
- **Fedora** - Modern, cutting-edge packages, ~200MB base
- **Arch** - Rolling release, latest software, ~400MB base

## Building Images

Build all images at once:
```bash
chmod +x build-all.sh
./build-all.sh
```

Build individual images:
```bash
# Alpine (default)
docker build -t ghost-labs-workspace:alpine -f ../workspace/Dockerfile ../workspace

# Ubuntu
docker build -t ghost-labs-workspace:ubuntu -f Dockerfile.ubuntu .

# Debian
docker build -t ghost-labs-workspace:debian -f Dockerfile.debian .

# Fedora
docker build -t ghost-labs-workspace:fedora -f Dockerfile.fedora .

# Arch
docker build -t ghost-labs-workspace:arch -f Dockerfile.arch .
```

## Image Contents

All images include:
- Git
- Vim & Nano editors
- curl & wget
- Build tools (gcc, make, etc.)
- Python 3 with pip
- Node.js with npm

## Usage

Users select their preferred OS when creating a new session. The container manager will use the corresponding image.

## Adding New OS

To add a new OS:
1. Create `Dockerfile.{osname}` in this directory
2. Follow the pattern from existing Dockerfiles
3. Add the OS to the `build-all.sh` script
4. Update this README
5. Update frontend OS selection options
