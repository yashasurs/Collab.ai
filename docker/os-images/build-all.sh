#!/bin/bash

echo "Building Ghost Labs OS Images..."
echo "================================="
echo ""

# Array of OS variants
declare -a OS_VARIANTS=("alpine" "ubuntu" "debian" "fedora" "arch")

for os in "${OS_VARIANTS[@]}"
do
    echo "Building $os image..."
    
    if [ "$os" = "alpine" ]; then
        # Alpine uses the original workspace Dockerfile
        docker build -t ghost-labs-workspace:$os -f ../workspace/Dockerfile ../workspace
    else
        # Other OS use their specific Dockerfiles
        docker build -t ghost-labs-workspace:$os -f Dockerfile.$os .
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully built ghost-labs-workspace:$os"
    else
        echo "❌ Failed to build ghost-labs-workspace:$os"
    fi
    echo ""
done

echo "================================="
echo "Build process complete!"
echo ""
echo "Available images:"
docker images | grep ghost-labs-workspace
