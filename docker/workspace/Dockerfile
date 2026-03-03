FROM alpine:3.19

# Install basic tools
RUN apk add --no-cache \
    bash \
    git \
    vim \
    nano \
    curl \
    wget \
    nodejs \
    npm \
    python3 \
    py3-pip \
    gcc \
    g++ \
    make

# Create workspace directory
WORKDIR /workspace

# Create a non-root user
RUN adduser -D -h /workspace ghostuser && \
    chown -R ghostuser:ghostuser /workspace

USER ghostuser

# Set up shell
ENV SHELL=/bin/bash

CMD ["/bin/bash"]
