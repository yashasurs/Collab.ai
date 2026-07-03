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
        docker build -t colab-$os:latest -f ../workspace/Dockerfile ../workspace
    else
        # Other OS use their specific Dockerfiles
        docker build -t colab-$os:latest -f Dockerfile.$os .
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully built colab-$os:latest"
    else
        echo "❌ Failed to build colab-$os:latest"
    fi
    echo ""
done

echo "================================="
echo "Build process complete!"
echo ""
echo "Available images:"
docker images | grep colab-
