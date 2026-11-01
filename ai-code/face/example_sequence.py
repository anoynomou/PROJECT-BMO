"""Run after `python app.py` to preview the expressions without UI buttons."""

import time

from client import FaceClient

face = FaceClient()

try:
    for emotion in ("happy", "love", "sad", "surprised", "angry", "shy", "curious"):
        face.start_emotion(emotion)
        time.sleep(2)

    face.start_emotion("happy")
    face.start_talking()
    time.sleep(3)
    face.stop_talking()

    face.start_listening()
    time.sleep(2)
    face.stop_listening()

    face.start_thinking()
    time.sleep(2)
    face.stop_thinking()

    face.start_sleeping()
    time.sleep(3)
    face.stop_sleeping()
finally:
    face.reset()
