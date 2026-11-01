# Raspberry Pi AI and face software

This directory contains two **independent** prototypes:

| Directory | What it does | Port | Status |
| --- | --- | --- | --- |
| [`face/`](face/) | Flask, full-screen BMO-inspired face; Python functions control expressions, talking, and sleep | `127.0.0.1:8766` | Current display face, no click controls |
| [`openai-prototype/`](openai-prototype/) | Earlier camera snapshot, microphone transcription, OpenAI response, speech, and its own face page | `127.0.0.1:8765` | Earlier experiment, not integrated with the current Flask face |

The OpenAI prototype's `face.html` has tap/keyboard interactions. Run `face/` to see the current no-button display. Starting both servers does not join their state automatically. The next integration step is to have the AI backend call `FaceClient` from `face/client.py` when a question starts, an answer arrives, and spoken audio plays.

Do not commit an API key. The older prototype reads `OPENAI_API_KEY` from the environment; see its README for setup. No local Qwen model is included yet.
