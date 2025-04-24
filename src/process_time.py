import json
import os
import sys
from datetime import datetime
import time
import threading
import win32gui
import win32process
import keyboard
import psutil
import ctypes
from ctypes import wintypes
from plyer import notification
import matplotlib.pyplot as plt

# loading config
def load_config_txt(config_path="config.txt"):
    # Default configuration
    defaults = {
        "time_limit": 60, # in seconds
        "idle_timeout": 120, # this too
        "log_file": "app_usage_log.json"
    }
    config = defaults.copy()

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in defaults:
                        # Cast to the appropriate type
                        if key == "time_limit" or key == "idle_timeout":
                            config[key] = int(value)
                        else:
                            config[key] = value
    return config

conf = load_config_txt()

LOG_FILE = conf["log_file"]
TIME_LIMIT = conf["time_limit"]
IDLE_TIMEOUT = conf["idle_timeout"]



def get_foreground_window():
    hwnd = win32gui.GetForegroundWindow()
    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process = psutil.Process(process_id)
        return process.name()
    except psutil.NoSuchProcess:
        return None

def send_notification(time_limit):
    notification.notify(
        title="ScreenMindr",
        message=f"Your usage time exceeded {time_limit} seconds. Consider taking a break.",
        timeout=10  # duration in seconds
    )

def is_computer_locked():
    WTS_CURRENT_SESSION = -1
    WTS_SESSIONSTATE = 14
    wtsapi32 = ctypes.WinDLL('wtsapi32', use_last_error=True)
    WTSQuerySessionInformation = wtsapi32.WTSQuerySessionInformationW
    WTSQuerySessionInformation.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(wintypes.WCHAR)),
        ctypes.POINTER(wintypes.DWORD)
    ]
    WTSQuerySessionInformation.restype = wintypes.BOOL

    buf = ctypes.POINTER(wintypes.WCHAR)()
    bytes_returned = wintypes.DWORD()

    if WTSQuerySessionInformation(
        None, WTS_CURRENT_SESSION, WTS_SESSIONSTATE, ctypes.byref(buf), ctypes.byref(bytes_returned)
    ):
        state = ctypes.wstring_at(buf)
        ctypes.windll.kernel32.LocalFree(buf)
        return state == 'Locked'
    return False

def is_idle():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        raise ctypes.WinError(ctypes.get_last_error())

    idle_time_ms = ctypes.windll.kernel32.GetTickCount() - last_input_info.dwTime

    idle_time_sec = idle_time_ms / 1000

    return idle_time_sec > IDLE_TIMEOUT

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=4)

def convert(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def track_usage(log):
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in log:
        log[today] = {"Total time": 0}
    daily_log = log[today]
    total_time = daily_log["Total time"]

    notified_limits = set()  # To track already notified time limits

    try:
        while True:
            if not is_computer_locked() and not is_idle():
                app_name = get_foreground_window()
                if app_name:
                    daily_log[app_name] = daily_log.get(app_name, 0) + 1
                    total_time += 1
                    daily_log["Total time"] = total_time

                    # Trigger notification for new limits
                    if total_time % TIME_LIMIT == 0 and total_time not in notified_limits:
                        send_notification(TIME_LIMIT)
                        notified_limits.add(total_time)

                sys.stdout.write(f"\rTotal time: {convert(total_time)}")
                sys.stdout.flush()
            save_log(log)
            time.sleep(1)
    except KeyboardInterrupt:
        save_log(log)
        print("\nExiting program...")

def display_stats(log):
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in log:
        print("No data for today.")
        return

    daily_log = log[today]
    if not daily_log:
        print("No data logged.")
        return

    labels = [k for k in daily_log.keys() if k != "Total time"]
    sizes = [daily_log[k] for k in labels]

    if not sizes:
        print("No usage data to display.")
        return

    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("App Usage Statistics", pad=32)
    plt.show()


def monitor_console(log):
    print("\nPress 'arrow_up + s' to display stats, 'arrow_up + q' to quit.")

    while True:
        if keyboard.is_pressed('up+q'):
            print("\n'Q' pressed. Exiting program...")
            os._exit(0)
        elif keyboard.is_pressed('up+s'):
            display_stats(log)


def main():
    log = load_log()
    tracker_thread = threading.Thread(target=track_usage, args=(log,))
    tracker_thread.daemon = True
    tracker_thread.start()

    monitor_console(log)

if __name__ == "__main__":
    main()
