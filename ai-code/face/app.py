"""BMO's display face. Import `face` from your own Python code."""

from __future__ import annotations

import threading
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.serving import make_server


EMOTIONS = frozenset({
    "neutral", "happy", "love", "sad", "surprised", "angry", "shy", "curious"
})
ACTIVITIES = frozenset({"idle", "listening", "thinking", "sleeping"})


class FaceController:
    """Thread-safe face state shared by the Flask display and Python callers."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._emotion = "neutral"
        self._activity = "idle"
        self._talking = False
        self._blink_seq = 0
        self._revision = 0

    def _change(self, *, emotion: str | None = None,
                activity: str | None = None,
                talking: bool | None = None) -> None:
        with self._lock:
            changed = False
            for name, value in (("_emotion", emotion), ("_activity", activity),
                                ("_talking", talking)):
                if value is not None and getattr(self, name) != value:
                    setattr(self, name, value)
                    changed = True
            if changed:
                self._revision += 1

    def start_emotion(self, emotion: str) -> None:
        """Show an emotion until changed or stopped (e.g. 'happy' or 'love')."""
        if emotion not in EMOTIONS:
            raise ValueError(f"Unknown emotion {emotion!r}. Choose from {sorted(EMOTIONS)}")
        with self._lock:
            self._change(emotion=emotion,
                         activity="idle" if self._activity == "sleeping" else None)

    set_emotion = start_emotion

    def stop_emotion(self) -> None:
        self._change(emotion="neutral")

    def start_talking(self) -> None:
        """Animate the mouth; the current emotion remains visible."""
        with self._lock:
            self._change(talking=True,
                         activity="idle" if self._activity == "sleeping" else None)

    def stop_talking(self) -> None:
        self._change(talking=False)

    def start_sleeping(self) -> None:
        self._change(activity="sleeping", talking=False)

    def stop_sleeping(self) -> None:
        with self._lock:
            if self._activity == "sleeping":
                self._change(activity="idle")

    def start_listening(self) -> None:
        self._change(activity="listening", talking=False)

    def stop_listening(self) -> None:
        with self._lock:
            if self._activity == "listening":
                self._change(activity="idle")

    def start_thinking(self) -> None:
        self._change(activity="thinking", talking=False)

    def stop_thinking(self) -> None:
        with self._lock:
            if self._activity == "thinking":
                self._change(activity="idle")

    def blink(self) -> None:
        """Trigger one extra blink. Natural blinks happen automatically."""
        with self._lock:
            self._blink_seq += 1
            self._revision += 1

    def reset(self) -> None:
        self._change(emotion="neutral", activity="idle", talking=False)

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "emotion": self._emotion, "activity": self._activity,
                "talking": self._talking, "blink_seq": self._blink_seq,
                "revision": self._revision,
            }


face = FaceController()
app = Flask(__name__)
_server = None
_server_thread = None


@app.get("/")
def display():
    return render_template("face.html")


@app.get("/api/state")
def state():
    response = jsonify(face.get_state())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/control")
def control():
    """Optional local HTTP bridge for Python code running in another process."""
    if request.remote_addr not in {"127.0.0.1", "::1"}:
        return jsonify(error="Local requests only"), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send a JSON object"), 400
    action = data.get("action")
    commands = {
        "start_emotion": lambda: face.start_emotion(data.get("emotion")),
        "set_emotion": lambda: face.set_emotion(data.get("emotion")),
        "stop_emotion": face.stop_emotion,
        "start_talking": face.start_talking,
        "stop_talking": face.stop_talking,
        "start_sleeping": face.start_sleeping,
        "stop_sleeping": face.stop_sleeping,
        "start_listening": face.start_listening,
        "stop_listening": face.stop_listening,
        "start_thinking": face.start_thinking,
        "stop_thinking": face.stop_thinking,
        "blink": face.blink,
        "reset": face.reset,
    }
    if action not in commands:
        return jsonify(error="Unknown action", actions=sorted(commands)), 400
    try:
        commands[action]()
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(face.get_state())


def start_server(host: str = "127.0.0.1", port: int = 8766) -> None:
    """Start the Flask display in a background thread, in this Python process."""
    global _server, _server_thread
    if _server is not None:
        return
    _server = make_server(host, port, app, threaded=True)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True,
                                      name="bmo-face-server")
    _server_thread.start()


def stop_server() -> None:
    """Stop a server started by start_server()."""
    global _server, _server_thread
    if _server is not None:
        _server.shutdown()
        _server.server_close()
        if _server_thread is not None:
            _server_thread.join(timeout=2)
        _server = None
        _server_thread = None


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8766, debug=False, use_reloader=False,
            threaded=True)
