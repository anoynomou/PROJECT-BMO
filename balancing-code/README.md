# ESP32 balancing firmware

This folder is reserved for the **tested** firmware that reads the LSM6DS3 IMU, estimates tilt, runs the balance controller, and commands the motor driver. Firmware has not been added yet.

The earlier prototype used an Arduino Uno, L298N, and TT motors; motor dead zone, brownouts, and frame shake were observed. The planned redesign uses an ESP32 and a driver chosen after checking the actual motor current (TB6612FNG or DRV8833 are candidates). Do not copy the old PID constants into the new frame without tuning.

## Firmware contract to implement

- Run IMU sampling and balance control locally on the ESP32, even if USB disconnects or the Pi is busy.
- Define startup calibration, tilt cutoff, motor disable, and recovery behavior before powered tests.
- Accept only high-level Pi commands over USB serial, such as mode or target speed; the Pi must not stream per-cycle motor PWM.
- Publish a versioned serial protocol, pin map, build instructions, and measured loop timing with the code.

Motor pins, gains, and voltage limits remain **TBD** until the hardware is confirmed.
