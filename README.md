# Project BMO

BMO is a two-wheel balancing robot with an expressive face, camera, microphone, speaker, and a separate motor controller. The Raspberry Pi handles the display and higher-level interaction. The ESP32 is intended to handle the balance loop and motors independently.

## Project map

| Folder | Purpose | Current state |
| --- | --- | --- |
| [`3d-model/`](3d-model/) | Body, screen mount, wheel and battery placement, CAD exports | Design area prepared; no CAD files have been added |
| [`balancing-code/`](balancing-code/) | ESP32 firmware, IMU, motor control, and USB serial protocol | Planning notes; no verified firmware has been added |
| [`ai-code/`](ai-code/) | Raspberry Pi face and camera/voice AI software | Working Flask face app plus an earlier, separate OpenAI prototype |
| [`electronics/`](electronics/) | Power, USB, sensor, motor-driver, and audio connections | System block diagram and a checklist; not a pin-level schematic |

## Software available now

The current face app is in [`ai-code/face/`](ai-code/face/). It fills the Pi display and is controlled from Python with `start_emotion`, `start_talking`, `start_sleeping`, and matching stop methods. It has no buttons. Its own README explains how to run it.

[`ai-code/openai-prototype/`](ai-code/openai-prototype/) contains the earlier camera, microphone, and ChatGPT API experiment. It serves a **different face** and has its own controls. These two applications have not yet been combined. See [`ai-code/README.md`](ai-code/README.md) before running either one.

## Intended system boundary

- **ESP32:** reads the IMU and drives the motor driver. Balancing must continue independently of network, camera, speech, or the Pi's browser.
- **Raspberry Pi:** shows the face, processes camera/audio, and sends high-level commands over USB serial when that protocol is implemented.
- **Power:** motor power and Pi power need their own correctly regulated paths. Verify the actual battery, regulators, motor driver, grounds, and current ratings before wiring.

See the [system overview](electronics/diagrams/system-overview.md). The diagram records the intended architecture, not a tested wiring plan.

## Next work

1. Add the real CAD source and dimensions to `3d-model/`.
2. Confirm the chosen ESP32, IMU, motor driver, pins, and power components; then draw and review the pin-level schematic.
3. Add tested ESP32 balance firmware and a documented Pi ↔ ESP32 serial protocol.
4. Connect the face app to the AI pipeline so speech playback drives the mouth and AI results drive expressions.

No API keys, credentials, or battery wiring assumptions belong in this repository.
