"""Control a running BMO face server from a separate Python process."""

import json
from urllib.request import Request, urlopen


class FaceClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8766") -> None:
        self.base_url = base_url.rstrip("/")

    def _send(self, action: str, emotion: str | None = None) -> dict:
        payload = {"action": action}
        if emotion is not None:
            payload["emotion"] = emotion
        request = Request(
            self.base_url + "/api/control",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def start_emotion(self, emotion: str) -> dict:
        return self._send("start_emotion", emotion)

    set_emotion = start_emotion

    def stop_emotion(self) -> dict:
        return self._send("stop_emotion")

    def start_talking(self) -> dict:
        return self._send("start_talking")

    def stop_talking(self) -> dict:
        return self._send("stop_talking")

    def start_sleeping(self) -> dict:
        return self._send("start_sleeping")

    def stop_sleeping(self) -> dict:
        return self._send("stop_sleeping")

    def start_listening(self) -> dict:
        return self._send("start_listening")

    def stop_listening(self) -> dict:
        return self._send("stop_listening")

    def start_thinking(self) -> dict:
        return self._send("start_thinking")

    def stop_thinking(self) -> dict:
        return self._send("stop_thinking")

    def blink(self) -> dict:
        return self._send("blink")

    def reset(self) -> dict:
        return self._send("reset")
