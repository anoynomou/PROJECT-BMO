#!/bin/sh
# Wait for BMO's local server before showing the face.
until python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1)' >/dev/null 2>&1; do
  sleep 1
done
exec chromium --kiosk --no-first-run --noerrdialogs --disable-infobars http://127.0.0.1:8765/
