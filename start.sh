#!/bin/bash
# Launching the virtual display (1920x1080 screen)
Xvfb :99 -screen 0 1920x1080x24 &

# Lightweight window environment (otherwise Firefox complains)
fluxbox &

# Launching the VNC server
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &

# noVNC (web interface, accessible via browser http://SERVER_IP:6080)
websockify --web=/usr/share/novnc 6080 localhost:5900 &

# export DISPLAY
export DISPLAY=:99

# launch worker
python3 worker.py