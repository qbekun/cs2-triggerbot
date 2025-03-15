# TriggerBot for CS2 with Arduino Integration

This is a simple **TriggerBot** script for **Counter-Strike 2 (CS2)** that automatically triggers mouse clicks when an enemy is in sight and you press the specified trigger key. It integrates with an **Arduino** device to send commands when a trigger action occurs.

## Requirements

- Python 3.x
- Required libraries:
  - `pymem`
  - `pynput`
  - `keyboard`
  - `colorama`
  - `pyserial`
  - `win32gui`
- **Counter-Strike 2** installed and running
- **Arduino** connected to your computer (adjust the COM port if necessary)

### Installation

1. Clone this repository or download the script.
2. Install the required libraries using pip:

```bash
pip install pymem pynput keyboard colorama pyserial pywin32
