import ctypes
from ctypes import wintypes
import time
import random
import serial
from serial.tools import list_ports
import requests
import re
import os

os.system('title /')

def parse_hpp(url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.text
    offsets = {}
    pattern = re.compile(r"(\w+)\s*=\s*(0x[0-9A-Fa-f]+)")
    for match in pattern.finditer(data):
        name, value = match.groups()
        offsets[name] = int(value, 16)
    return offsets

offsets_hpp = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.hpp"
client_hpp  = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.hpp"

try:
    offsets = parse_hpp(offsets_hpp)
    client  = parse_hpp(client_hpp)

    offset_map = {
        "entity_list": offsets["dwEntityList"],
        "local_player": offsets["dwLocalPlayerPawn"],
        "health": client["m_iHealth"],
        "team_number": client["m_iTeamNum"],
        "entity_index": client["m_iIDEntIndex"],
    }
except Exception as e:
    exit()

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE  = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
PROCESS_ALL_ACCESS = 0x1F0FFF
MAX_PATH = 260

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', wintypes.CHAR * MAX_PATH)
    ]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('th32ModuleID', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('GlblcntUsage', wintypes.DWORD),
        ('ProccntUsage', wintypes.DWORD),
        ('modBaseAddr', ctypes.POINTER(ctypes.c_byte)),
        ('modBaseSize', wintypes.DWORD),
        ('hModule', wintypes.HMODULE),
        ('szModule', ctypes.c_char * 256),
        ('szExePath', ctypes.c_char * MAX_PATH)
    ]

CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
Process32First = kernel32.Process32First
Process32Next = kernel32.Process32Next
Module32First = kernel32.Module32First
Module32Next = kernel32.Module32Next
OpenProcess = kernel32.OpenProcess
ReadProcessMemory = kernel32.ReadProcessMemory
CloseHandle = kernel32.CloseHandle

CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
CreateToolhelp32Snapshot.restype = wintypes.HANDLE

Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32First.restype = wintypes.BOOL

Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32Next.restype = wintypes.BOOL

Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
Module32First.restype = wintypes.BOOL

Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
Module32Next.restype = wintypes.BOOL

OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL

CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

def find_pid_by_name(proc_name):
    name = proc_name.lower()
    hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if hSnap == ctypes.c_void_p(-1).value:
        return 0
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    pid = 0
    try:
        if not Process32First(hSnap, ctypes.byref(entry)):
            return 0
        while True:
            exe = bytes(entry.szExeFile).split(b'\x00',1)[0].decode(errors='ignore').lower()
            if exe == name or exe == name + '.exe':
                pid = entry.th32ProcessID
                break
            if not Process32Next(hSnap, ctypes.byref(entry)):
                break
    finally:
        CloseHandle(hSnap)
    return pid

def get_module_base(pid, module_name):
    mod = module_name.lower()
    hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if hSnap == ctypes.c_void_p(-1).value:
        return 0
    me32 = MODULEENTRY32()
    me32.dwSize = ctypes.sizeof(MODULEENTRY32)
    base = 0
    try:
        if not Module32First(hSnap, ctypes.byref(me32)):
            return 0
        while True:
            name = bytes(me32.szModule).split(b'\x00',1)[0].decode(errors='ignore').lower()
            if name == mod or name == mod.replace('.dll',''):
                base = ctypes.cast(me32.modBaseAddr, ctypes.c_void_p).value
                break
            if not Module32Next(hSnap, ctypes.byref(me32)):
                break
    finally:
        CloseHandle(hSnap)
    return base

class ProcessMemory:
    def __init__(self, pid):
        self.handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)

    def read_bytes(self, address, size):
        buf = (ctypes.c_ubyte * size)()
        bytesRead = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buf), size, ctypes.byref(bytesRead))
        if not ok:
            return None
        return bytes(buf[:bytesRead.value])

    def read_longlong(self, address):
        b = self.read_bytes(address, 8)
        return int.from_bytes(b, 'little', signed=False) if b else 0

    def read_int(self, address):
        b = self.read_bytes(address, 4)
        return int.from_bytes(b, 'little', signed=True) if b else 0

    def close(self):
        if self.handle:
            CloseHandle(self.handle)
            self.handle = None

arduino = None
arduino_port = None
last_connection_status = None

def find_arduino_port():
    ports = [
        p.device for p in list_ports.comports()
        if 'arduino' in p.description.lower() or 'ch340' in p.description.lower() or 'usb serial device' in p.description.lower()
    ]
    return ports[0] if ports else None

def connect_arduino():
    global arduino, arduino_port, last_connection_status
    try:
        if arduino and arduino.is_open:
            arduino.close()
        arduino_port = find_arduino_port()
        if arduino_port:
            arduino = serial.Serial(arduino_port, 115200, timeout=1)
            time.sleep(0.2)
            if last_connection_status != "connected":
                print(f"connected to the device. {arduino_port}")
                last_connection_status = "connected"
            return True
        else:
            if last_connection_status != "disconnected":
                print("device not found, retrying...")
                last_connection_status = "disconnected"
            return False
    except Exception:
        if last_connection_status != "disconnected":
            print("device not found, retrying...")
            last_connection_status = "disconnected"
        return False

def send_mouse_click():
    if arduino and arduino.is_open:
        try:
            arduino.write(b"loli\n")
            return True
        except Exception:
            return False
    return False

def is_alt_pressed():
    return user32.GetAsyncKeyState(0x12) & 0x8000 != 0

def is_window_active(title_substring):
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_string_buffer(256)
    user32.GetWindowTextA(hwnd, buf, 256)
    return title_substring.encode() in buf.value

def main():
    proc_name = "cs2.exe"
    module_name = "client.dll"

    pid = find_pid_by_name(proc_name)
    if not pid:
        return
    base = get_module_base(pid, module_name)
    if not base:
        return

    pm = ProcessMemory(pid)
    arduino_connected = connect_arduino()

    try:
        while True:
            if not is_window_active("Counter-Strike 2"):
                time.sleep(0.05)
                continue

            if is_alt_pressed():
                player = pm.read_longlong(base + offset_map["local_player"])
                if not player:
                    time.sleep(0.01)
                    continue

                entity_id = pm.read_int(player + offset_map["entity_index"])
                if entity_id > 0:
                    entity_list = pm.read_longlong(base + offset_map["entity_list"])
                    entry = pm.read_longlong(entity_list + 0x8 * (entity_id >> 9) + 0x10)
                    entity = pm.read_longlong(entry + 120 * (entity_id & 0x1FF))

                    if entity:
                        entity_team = pm.read_int(entity + offset_map["team_number"])
                        entity_health = pm.read_int(entity + offset_map["health"])
                        player_team = pm.read_int(player + offset_map["team_number"])

                        if entity_team != player_team and entity_health > 0:
                            time.sleep(random.uniform(0.025, 0.08))
                            if not send_mouse_click():
                                arduino_connected = connect_arduino()
                            time.sleep(random.uniform(0.01, 0.035))
            time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        pm.close()
        try:
            if arduino and arduino.is_open:
                arduino.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
