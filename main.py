import pymem, time, ctypes, pymem.process, os, sys
from requests import get
import serial
from colorama import init, Fore, Style


init(autoreset=True)

# Initialize serial communication with Arduino
arduino = serial.Serial('COM9', 115200)

def fetch_data():
    offset_data = get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json")
    client_data = get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json")
    return (
        offset_data.json() if offset_data.status_code == 200 else None,
        client_data.json() if client_data.status_code == 200 else None,
    )

def get_memory_handle():
    try:
        pm = pymem.Pymem("cs2.exe")
        client_module = pymem.process.module_from_name(pm.process_handle, "client.dll")
        return pm, client_module.lpBaseOfDll if client_module else None
    except pymem.exception.PymemError as e:
        print(f"[{Fore.RED}!{Fore.RESET}] {str(e).lower()}")
        input()
        sys.exit(1)
        return None, None

def read_memory(pm, base, offsets):
    local_player = pm.read_longlong(base + offsets["local_player"])
    entity_id = pm.read_int(local_player + offsets["entity_index"])
    if entity_id <= 0:
        return None, None, None
    entity_list = pm.read_longlong(base + offsets["entity_list"])
    entity_entry = pm.read_longlong(entity_list + 0x8 * (entity_id >> 9) + 0x10)
    entity = pm.read_longlong(entity_entry + 120 * (entity_id & 0x1FF))
    return (
        entity,
        pm.read_int(local_player + offsets["team_number"]),
        pm.read_int(entity + offsets["team_number"]) if entity else None,
    )

def attack(entity, entity_health):
    if entity and entity_health > 0:
        time.sleep(0.001)
        arduino.write(b'loli\n')

def run():
    offsets, client_data = fetch_data()
    if not offsets or not client_data:
        return

    offset_map = {
        "entity_list": offsets["client.dll"]["dwEntityList"],
        "local_player": offsets["client.dll"]["dwLocalPlayerPawn"],
        "health": client_data["client.dll"]["classes"]["C_BaseEntity"]["fields"]["m_iHealth"],
        "team_number": client_data["client.dll"]["classes"]["C_BaseEntity"]["fields"]["m_iTeamNum"],
        "entity_index": client_data["client.dll"]["classes"]["C_CSPlayerPawnBase"]["fields"]["m_iIDEntIndex"],
    }

    pm, base = get_memory_handle()
    if not pm or not base:
        return
    print(f"[{Fore.GREEN}+{Fore.RESET}] loaded, open cs2.exe")

    while True:
        print(f"[{Fore.GREEN}+{Fore.RESET}] log: WAITING         ", end='\r')
        if ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000:  # Left Shift key
            entity, player_team, entity_team = read_memory(pm, base, offset_map)
            if entity:
                try:
                    entity_health = pm.read_int(entity + offset_map["health"])
                    if entity_team != player_team:
                        attack(entity, entity_health)
                except Exception as e:
                    print(f"[{Fore.RED}!{Fore.RESET}] error reading entity health: {e}")
            else:
                print(f"[{Fore.RED}!{Fore.RESET}] no valid entity found.", end='\r')

        time.sleep(0.001)

if __name__ == "__main__":
    run()
