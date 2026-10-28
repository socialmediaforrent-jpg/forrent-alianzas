#!/bin/bash
# nohup ./sync_loop.sh >> sync.log 2>&1 &
cd /workspace/forrent/alianzas_web; python3 sync_render.py --push-only || true
while true; do sleep 300; python3 sync_render.py || true; done
