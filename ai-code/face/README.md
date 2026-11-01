# BMO face for Raspberry Pi

A full-screen, BMO-inspired animated face. Its default expression follows your first reference: two small oval eyes and a short smile on a pale mint screen. The HTML has no buttons or click controls. Python drives the face.

## Run it

From this folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

On the Pi, open `http://127.0.0.1:8766` in Chromium and press F11 for full screen. A kiosk launch can use:

```bash
chromium --kiosk --noerrdialogs http://127.0.0.1:8766
```

The server listens on loopback only. The display and any separate Python controller must run on the same Pi. The port is **8766**, leaving 8765 free if you use the earlier AI starter.

## From another function in the same Python process

```python
from app import face, start_server, stop_server

start_server()  # starts the display server in a background thread

face.start_emotion("happy")
face.start_talking()       # call when audio starts playing
# ... play speech ...
face.stop_talking()        # call when audio finishes
face.stop_emotion()        # return to the first-reference default face

stop_server()              # optional on program exit
```

If you run `python app.py` as the display server, import `face` only into code running **inside that same process**. A separate process should use `FaceClient` below; importing `app.face` in another process makes a separate state.

## From a separate AI or camera process

Run `python app.py` first. Then:

```python
from client import FaceClient

face = FaceClient()

def on_question():
    face.start_listening()

def on_thinking():
    face.stop_listening()
    face.start_thinking()

def on_reply(text, mood):
    face.stop_thinking()
    face.start_emotion(mood)  # e.g. "happy", "curious", "sad"
    face.start_talking()
    try:
        speak(text)             # replace with your text-to-speech function
    finally:
        face.stop_talking()

def on_idle():
    face.stop_emotion()
```

The page reacts to Python state changes within about 0.2 seconds. It does not call an AI service or access a camera by itself; your AI/camera functions select the emotion and call these methods. `start_talking()` cycles through a line, dot, narrow slit, and green oval mouth with varied timing until `stop_talking()`; it does not analyze microphone audio.

## Commands

| Start | Stop / reset | Effect |
| --- | --- | --- |
| `start_emotion("happy")` | `stop_emotion()` | Happy, love, sad, surprised, angry, shy, curious, neutral |
| `start_talking()` | `stop_talking()` | Animated mouth over the selected emotion |
| `start_sleeping()` | `stop_sleeping()` | Closed eyes and drifting Zs |
| `start_listening()` | `stop_listening()` | Gentle side rings |
| `start_thinking()` | `stop_thinking()` | Small drifting dots |
| `blink()` | — | One extra blink; natural blinks are automatic |
| `reset()` | — | Neutral, idle, silent |

For a hands-free preview, open the page and run `.venv/bin/python example_sequence.py` in another terminal. There are no browser input bindings.
