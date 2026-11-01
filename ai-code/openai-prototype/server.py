"""BMO's local Pi server. Bind to loopback; the API key never enters the browser."""
import base64
import io
import json
import logging
import os
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.getenv("BMO_PORT", "8765"))
MODEL = os.getenv("BMO_MODEL", "gpt-4.1-mini")
VOICE = os.getenv("BMO_VOICE", "coral")
OBSERVE_SECONDS = max(0, int(os.getenv("BMO_OBSERVE_SECONDS", "90")))
LOG = logging.getLogger("bmo")
LOCK = threading.Lock()
HISTORY = []
CAMERA = None
CLIENT = None


class Reply(BaseModel):
    answer: str = Field(description="A warm, concise reply of at most 70 words")
    mood: Literal["curious", "happy", "sad", "surprised", "sleepy", "love", "grumpy"]


def client():
    global CLIENT
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from the Pi service environment.")
    if CLIENT is None:
        CLIENT = OpenAI(timeout=35.0, max_retries=1)
    return CLIENT


def camera_frame():
    """Capture one JPEG from the CSI camera; keep the camera warm between requests."""
    global CAMERA
    if CAMERA is None:
        try:
            from picamera2 import Picamera2
            CAMERA = Picamera2()
            CAMERA.configure(CAMERA.create_still_configuration(main={"size": (640, 480)}))
            CAMERA.start()
            time.sleep(0.8)
        except Exception as exc:
            CAMERA = None
            raise RuntimeError("Pi camera unavailable. Check its ribbon cable and run rpicam-hello.") from exc
    try:
        image = io.BytesIO()
        CAMERA.capture_file(image, format="jpeg")
        return image.getvalue()
    except Exception as exc:
        try:
            CAMERA.stop()
        except Exception:
            pass
        CAMERA = None
        raise RuntimeError("Could not capture a frame from the Pi camera.") from exc


def transcribe(audio_bytes):
    if len(audio_bytes) > 10_000_000:
        raise ValueError("Recording is too large. Try a shorter question.")
    # The transcription endpoint uses the file extension to identify WebM audio.
    with tempfile.NamedTemporaryFile(suffix=".webm") as audio:
        audio.write(audio_bytes)
        audio.flush()
        with open(audio.name, "rb") as source:
            result = client().audio.transcriptions.create(
                model="gpt-4o-mini-transcribe", file=source
            )
    return result.text.strip()


def think(question, image, observe=False):
    instruction = (
        "You are BMO, a curious, kind robot. Reply naturally and briefly. "
        "The attached camera frame is a single moment, not live video. "
        "Only describe things that are visible; admit uncertainty. "
        "Do not claim to know a person's identity, intention, or feelings from appearance. "
        "Choose a mood appropriate to your response or the visible scene. "
        "Use grumpy only for playful annoyance. No motor or GPIO commands."
    )
    if observe:
        instruction += " This is a quiet observation. Give one short, interesting observation; do not ask a question."
    content = [{"type": "input_text", "text": question}]
    if image:
        content.append({
            "type": "input_image",
            "image_url": "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii"),
            "detail": "low",
        })
    context = [] if observe else HISTORY[-6:]
    result = client().responses.parse(
        model=MODEL,
        instructions=instruction,
        input=[*context, {"role": "user", "content": content}],
        text_format=Reply,
        store=False,
    )
    if not result.output_parsed:
        raise RuntimeError("BMO could not form a reply. Please try again.")
    reply = result.output_parsed
    if not observe:
        HISTORY.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": reply.answer},
        ])
        del HISTORY[:-6]
    return reply


def speech_bytes(answer):
    # Speech is generated on the Pi, then delivered to the local face UI.
    with client().audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice=VOICE, input=answer[:1200],
        instructions="Speak warmly, with a friendly curious robot personality.",
        response_format="mp3",
    ) as response:
        return response.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        LOG.info("%s - %s", self.client_address[0], format_string % args)

    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/face.html"):
            data = (ROOT / "face.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/health":
            self.send_json(200, {"status": "ready", "observe_seconds": OBSERVE_SECONDS,
                                 "api_key_present": bool(os.getenv("OPENAI_API_KEY"))})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path not in ("/api/ask", "/api/observe"):
            self.send_error(404)
            return
        if not LOCK.acquire(blocking=False):
            self.send_json(429, {"error": "BMO is still thinking. Try again shortly."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 14_000_000:
                raise ValueError("Request size is invalid or too large.")
            request = json.loads(self.rfile.read(length))
            observe = self.path == "/api/observe"
            if observe and not OBSERVE_SECONDS:
                self.send_json(403, {"error": "Automatic observations are disabled."})
                return
            question = str(request.get("question", "")).strip()[:500]
            if request.get("audio") and not observe:
                audio = base64.b64decode(request["audio"], validate=True)
                question = transcribe(audio)[:500]
            if not question and not observe:
                raise ValueError("I didn't hear a question. Please try again.")
            if observe:
                question = "Make a brief observation about what you can see now."
            try:
                image = camera_frame()
            except RuntimeError as exc:
                if observe:
                    raise
                LOG.warning("Camera unavailable; answering text only: %s", exc)
                image = None
            reply = think(question, image, observe)
            payload = {"answer": reply.answer, "mood": reply.mood,
                       "question": question, "camera_used": image is not None}
            if not observe:
                try:
                    payload["audio"] = base64.b64encode(speech_bytes(reply.answer)).decode("ascii")
                except Exception as exc:
                    LOG.warning("Speech unavailable: %s", exc)
                    payload["audio"] = None
            self.send_json(200, payload)
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
        except Exception as exc:
            LOG.exception("Request failed")
            # The browser receives a simple error without API credentials or stack traces.
            self.send_json(503, {"error": str(exc) if isinstance(exc, RuntimeError) else
                                 "BMO could not reach the AI service. Check the Pi log."})
        finally:
            LOCK.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOG.info("BMO ready at http://%s:%d", HOST, PORT)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
