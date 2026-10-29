# Desktop Linux livre; NENHUM instalador DaVinci ou driver proprietario.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb openbox xterm x11vnc novnc websockify xauth openssl x11-utils iproute2 \
    mesa-utils libgl1-mesa-dri clinfo ffmpeg python3 python3-venv \
    procps curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
