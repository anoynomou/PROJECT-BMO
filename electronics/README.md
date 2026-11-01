# Electronics

The [system block diagram](diagrams/system-overview.md) shows the intended power and data paths. It is **not** a pin-level wiring diagram or a verified electrical schematic. No motor-driver pin map or regulator settings have been confirmed in this repository.

Before a pin-level schematic is added, record exact part numbers and ratings for the battery, fuses, buck regulators, Raspberry Pi, ESP32 board, LSM6DS3 breakout, motor driver, motors, amplifier, and speaker. Measure and label each regulated voltage and document the common ground and USB power behavior.

Keep the ESP32 balance loop independent of the Pi. The USB cable is for serial communication; motor power must be sized and wired through its own regulator/driver path.
