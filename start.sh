#!/bin/bash
# Launching the virtual display (1920x1080 screen)
Xvfb :100 -screen 0 1920x1080x24 &

# Lightweight window environment (otherwise Firefox complains)
fluxbox &

# Launching the VNC server
x11vnc -display :100 -nopw -forever -shared -rfbport 5901 &

# noVNC (web interface, accessible via browser http://SERVER_IP:6080)
websockify --web=/usr/share/novnc 6081 localhost:5901 &

# export DISPLAY
export DISPLAY=:100

# launch worker
python3 worker.py