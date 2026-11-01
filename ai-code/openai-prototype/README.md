# BMO AI face for Raspberry Pi

The Pi runs the face, captures a still camera frame, and talks to the OpenAI API. A response includes an answer and a mood; BMO animates her face and speaks the answer. The ESP32 can remain a separate balance controller over USB serial. This starter does **not** issue motor commands.

## Hardware

- Raspberry Pi 4/5 running a current Raspberry Pi OS **Desktop** image, with internet access.
- Pi Camera connected by its ribbon cable to the camera port, and a working speaker/audio output.
- For spoken questions, add a USB microphone (or other microphone recognized by the Pi). Until then, press **T** to type a question. Tap the face to speak; tap again to finish. Hold the face to ask BMO to look around. There are no permanent mood buttons.
- The camera sends **one still JPEG** to the API per question or idle observation. This starter does not stream video to the API.

## Install on the Pi

Extract this ZIP into your home directory so the path is `~/bmo-ai/server.py`.

1. Confirm the camera works: `rpicam-hello --timeout 2000`. On recent Raspberry Pi OS, install Picamera2 if needed with `sudo apt install python3-picamera2`.
2. Run:

```bash
cd ~/bmo-ai
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
```

3. Create an OpenAI API key in the OpenAI platform. API usage requires its own billing; a ChatGPT subscription does not supply API credits. Keep the key on the Pi. Create `~/.config/bmo.env` with this one line:

```text
OPENAI_API_KEY=YOUR_KEY_HERE
```

Then restrict access: `chmod 600 ~/.config/bmo.env`.

4. Test manually before setting up boot startup:

```bash
cd ~/bmo-ai
set -a
. ~/.config/bmo.env
set +a
.venv/bin/python server.py
```

Open `http://127.0.0.1:8765/` in Chromium **on the Pi**. Ask a typed question with **T**, or tap the face if a microphone is installed. The captured image is used with the question; ask “What do you see?” to test it. `Ctrl+C` stops the manual server.

## Start automatically

Use Desktop Auto Login in Raspberry Pi Configuration. Copy the bundled service and enable it:

```bash
mkdir -p ~/.config/systemd/user ~/.config/labwc
cp ~/bmo-ai/bmo.service ~/.config/systemd/user/bmo.service
systemctl --user daemon-reload
systemctl --user enable --now bmo.service
```

Add the following **one line** at the end of `~/.config/labwc/autostart`:

```bash
$HOME/bmo-ai/start_kiosk.sh &
```

The launcher waits for the local server, then opens Chromium in kiosk mode. Reboot to check. `systemctl --user status bmo.service` and `journalctl --user -u bmo.service -n 50` help diagnose startup problems. If your Pi uses a different desktop/window manager, its autostart path may differ.

## Behavior and cost

`BMO_OBSERVE_SECONDS=90` is the default. While idle, BMO captures a still frame about every 90 seconds and chooses a mood and brief observation. That **uses an API request each time**. Add `BMO_OBSERVE_SECONDS=0` to `~/.config/bmo.env` to turn off idle observations. Restart with `systemctl --user restart bmo.service`. You can change the answer model with `BMO_MODEL=gpt-4.1-mini` and voice with `BMO_VOICE=coral` in the same file.

The face is served only on `127.0.0.1`, so the API key never goes into browser JavaScript. The Pi needs internet for transcription, visual understanding, and generated speech. The face remains visible if the internet fails, but AI answers will pause. Keep a separate emergency stop and independent balance control on the ESP32 before connecting motors.

The voice you hear from BMO is AI generated.

## References

- [OpenAI vision inputs](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI speech transcription](https://developers.openai.com/api/docs/guides/speech-to-text)
- [OpenAI speech generation](https://developers.openai.com/api/docs/guides/text-to-speech)
- [Raspberry Pi Picamera2](https://www.raspberrypi.com/documentation/computers/camera_software.html)
- [Raspberry Pi kiosk startup](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/)
