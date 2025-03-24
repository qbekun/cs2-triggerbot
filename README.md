# CS2 TriggerBot with Arduino Integration

This repository contains a Python-based TriggerBot for Counter-Strike 2 (CS2) that uses **pymem** for memory reading and **Arduino** for simulating mouse clicks. The bot is designed to automatically shoot enemies when they are in sight.

## Features

- **TriggerBot**: Automatically shoots when an enemy is within your crosshair.
- **Arduino Integration**: Sends a mouse click command via serial communication to the Arduino for simulating mouse clicks.
- **Memory Reading**: Reads CS2 memory offsets to track player and enemy data.
- **Shift Key Activation**: The bot is activated when the **Left Shift** key is held down.
- **Colorful Output**: Uses `colorama` to provide colorful console output.

## Requirements

- **Python 3.x**: The script is written in Python.
- **Arduino**: An Arduino device is required for simulating mouse clicks. Make sure you have the correct serial port set up.
- **Libraries**:
  - `pymem`
  - `requests`
  - `pyserial`
  - `colorama`
  - `ctypes` (built-in)
  
  You can install the required libraries using `pip`:

  ```bash
  pip install pymem requests pyserial colorama
