import pymem
import pymem.process
import keyboard
import time
import os
import serial
from pynput.mouse import Controller, Button
from win32gui import GetWindowText, GetForegroundWindow
from random import uniform
from colorama import Fore, Back, Style, init  # Import colorama for color support
from offsets import *

# Initialize Colorama
init(autoreset=True)

# Set up serial communication with Arduino (replace 'COM3' with the correct port for your system)
arduino = serial.Serial('COM8', 115200)  # Adjust the COM port as needed

# Initialize mouse controller
mouse = Controller()

# Offsets for CS2
client = Client()
dwEntityList = client.offset('dwEntityList')
dwLocalPlayerPawn = client.offset('dwLocalPlayerPawn')
m_iIDEntIndex = client.get('C_CSPlayerPawnBase', 'm_iIDEntIndex')
m_iTeamNum = client.get('C_BaseEntity', 'm_iTeamNum')
m_iHealth = client.get('C_BaseEntity', 'm_iHealth')

triggerKey = "shift"

# Function to send commands to Arduino via serial
def send_command(command):
    arduino.write(f"{command}\n".encode())  # Send command to Arduino

def main():
    print(Fore.CYAN + f"[-] TriggerBot started.\n[-] Trigger key: {triggerKey.upper()}")  # Display startup message in cyan
    try:
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
    except:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(Fore.RED + "❌ Please open CS2! ❌")  # Error message in red
        exit()

    while True:
        try:
            if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":
                continue

            if keyboard.is_pressed(triggerKey):
                player = pm.read_longlong(client + dwLocalPlayerPawn)
                entityId = pm.read_int(player + m_iIDEntIndex)

                if entityId > 0:
                    entList = pm.read_longlong(client + dwEntityList)

                    entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
                    entity = pm.read_longlong(entEntry + 120 * (entityId & 0x1FF))

                    entityTeam = pm.read_int(entity + m_iTeamNum)
                    playerTeam = pm.read_int(player + m_iTeamNum)

                    if entityTeam != playerTeam:
                        entityHp = pm.read_int(entity + m_iHealth)
                        if entityHp > 0:
                            # Send mouse click command to Arduino
                            send_command("loli")
                            time.sleep(uniform(0.01, 0.05))  # Adjust time as needed

                time.sleep(0.03)
            else:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(Fore.YELLOW + "[INFO] TriggerBot stopped.")  # Yellow message when stopped
            break
        except:
            print(Fore.RED + "[ERROR] An unexpected error occurred!")  # Error message in red
            pass

if __name__ == '__main__':
    main()
