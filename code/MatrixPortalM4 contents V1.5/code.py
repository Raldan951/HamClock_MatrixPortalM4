# HamClockV1.5: FT8, General, Settings, World Modes with Buttons - Hybrid BMP/Code
# Created collaboratively by Pete Parise and Grok (xAI), Feb 2025
# A hybrid display solution for the Matrix Portal M4 using CircuitPython 8.2.10.
# Features:
# - Compiled BMP sprites (tx_red.bmp, tx_blue.bmp) for TX boxes with gamma-adjusted colors,
#   solving bit-depth rendering issues from earlier versions.
# - Code-generated Bitmap/Palette graphics for line, drift, and dots, reverting to proven methods.
# - Four modes: FT8 (TX toggle), General, Settings, World (with added line/drift/dots, centered time).
# - Built through iterative troubleshooting, leveraging Pete's insights on LED gamma and mode design.
# First of hopefully many joint projects—capturing time, creativity, and pixel precision!
import board
import time
import displayio
import digitalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import terminalio
from adafruit_display_text import label
import os
from displayio import Palette, Bitmap

displayio.release_displays()
time.sleep(1)

matrix = Matrix(width=64, height=32, bit_depth=2)
display = matrix.display

try:
    from secrets import secrets
except ImportError:
    print("Wi-Fi secrets missing! Using fallback time.")
    secrets = {'ssid': '', 'password': ''}

button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP
button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

def fetch_time():
    """Fetch current time from Adafruit IO NTP service."""
    try:
        current_time = network.get_local_time()
        if isinstance(current_time, str):
            time_parts = current_time.split(" ")
            time_str = time_parts[1]
            hours, minutes, seconds_ms = time_str.split(":")
            seconds, ms = seconds_ms.split(".")
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(ms) / 1000
            return (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
        else:
            return current_time.tm_hour, current_time.tm_min, current_time.tm_sec
    except Exception:
        return None

def load_sync_interval():
    try:
        with open("/sync_interval.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 3600

def save_sync_interval(interval):
    try:
        with open("/sync_interval.txt", "w") as f:
            f.write(str(interval))
    except:
        pass

try:
    network = Network(status_neopixel=board.NEOPIXEL, debug=True)
    time.sleep(5)
except Exception as e:
    print(f"Network failed: {e}. Running offline.")
    network = None

ntp_time = fetch_time() or (0, 0, 0)
initial_hours, initial_minutes, initial_seconds = ntp_time
start_mono = time.monotonic()
last_sync = start_mono
sync_interval = load_sync_interval()
last_drift_check = start_mono
drift_threshold = 1

# Display Elements (Your Line Numbers)
local_label = label.Label(terminalio.FONT, text="00:00:00", color=0x005500, x=8, y=8)  # 76
utc_label = label.Label(terminalio.FONT, text="00:00:00", color=0x555500, x=8, y=24)   # 77
# Code-Generated Line
line_palette = Palette(2)                                                               # 78
line_palette[0] = 0x000000                                                              # 79
line_palette[1] = 0x006600  # Adjusted green                                           # 80
line_bitmap = Bitmap(64, 2, 1)                                                         # 81
for x in range(64):                                                                    # 82
    line_bitmap[x, 0] = 1                                                              # 83
    line_bitmap[x, 1] = 1                                                              # 84
line_sprite = displayio.TileGrid(line_bitmap, pixel_shader=line_palette, x=0, y=15)    # 85
# Code-Generated Drift
drift_palette = Palette(2)                                                             # 86
drift_palette[0] = 0x000000                                                            # 87
drift_palette[1] = 0x000066  # Adjusted blue                                          # 88
drift_bitmap = Bitmap(1, 2, 1)                                                        # 89
drift_bitmap[0, 0] = 1                                                                # 90
drift_bitmap[0, 1] = 1                                                                # 91
drift_sprite = displayio.TileGrid(drift_bitmap, pixel_shader=drift_palette, x=32, y=15)  # 92
# Code-Generated Dot
dot_palette = Palette(2)                                                              # 93
dot_palette[0] = 0x000000                                                             # 94
dot_palette[1] = 0x006600  # Adjusted green                                          # 95
dot_bitmap = Bitmap(1, 1, 1)                                                         # 96
dot_bitmap[0, 0] = 1                                                                 # 97
dot_above_sprite = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=14)  # 98
dot_below_sprite = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=17)  # 99
# Compiled TX BMPs
tx_red = displayio.OnDiskBitmap("/tx_red.bmp")                                       # 100
tx_red_sprite = displayio.TileGrid(tx_red, pixel_shader=tx_red.pixel_shader, x=55, y=0)  # 101
tx_blue = displayio.OnDiskBitmap("/tx_blue.bmp")                                     # 102
tx_blue_sprite = displayio.TileGrid(tx_blue, pixel_shader=tx_blue.pixel_shader, x=55, y=0)  # 103
settings_label = label.Label(terminalio.FONT, text="PST", color=0xFFFFFF, x=20, y=16)  # 104

group = displayio.Group()
mode = 0  # 0: FT8, 1: General, 2: Settings, 3: World
ft8_tx_mode = 0  # 0: Even, 1: Odd
settings_tz = 0  # 0: PST, 1: UTC, 2: EST
world_tz = 0  # 0: GMT, 1: EST, 2: CST

def display_ft8(local_str, utc_str, sec_in_minute, tx_mode):
    while len(group) > 0:
        group.pop()
    group.append(local_label)
    group.append(utc_label)
    group.append(line_sprite)
    group.append(drift_sprite)
    group.append(dot_above_sprite)
    group.append(dot_below_sprite)
    if tx_mode == 0:  # Even - Red/dark red
        group.append(tx_red_sprite)
    else:  # Odd - Blue/dark blue
        group.append(tx_blue_sprite)
    local_label.x = 4
    utc_label.x = 4
    utc_label.text = utc_str
    if tx_mode == 0:
        tx_red_sprite.y = 0 if (0 <= sec_in_minute <= 14 or 30 <= sec_in_minute <= 44) else 17
    else:
        tx_blue_sprite.y = 0 if (15 <= sec_in_minute <= 29 or 45 <= sec_in_minute <= 59) else 17

def display_general(local_str, utc_str, sec_in_minute):
    while len(group) > 0:
        group.pop()
    group.append(local_label)
    group.append(line_sprite)
    group.append(drift_sprite)
    group.append(dot_above_sprite)
    group.append(dot_below_sprite)
    group.append(utc_label)
    local_label.x = 8
    utc_label.x = 8
    local_label.y = 8
    utc_label.y = 24
    utc_label.text = utc_str

def display_settings(tz_index):
    while len(group) > 0:
        group.pop()
    group.append(settings_label)
    settings_label.x = 20
    tz_names = ["PST", "UTC", "EST"]
    settings_label.text = tz_names[tz_index]

def display_world(local_str, total_seconds, tz_index):
    while len(group) > 0:
        group.pop()
    group.append(local_label)
    group.append(utc_label)
    group.append(line_sprite)
    group.append(drift_sprite)
    group.append(dot_above_sprite)
    group.append(dot_below_sprite)
    local_label.x = 8
    utc_label.x = 5  # Adjusted centering
    tz_offsets = [8, 3, 2]  # GMT (UTC), EST (UTC-5), CST (UTC-6) from PST
    tz_names = ["GMT", "EST", "CST"]
    world_hours = int((total_seconds + tz_offsets[tz_index] * 3600) // 3600) % 24
    world_minutes = int((total_seconds + tz_offsets[tz_index] * 3600) // 60) % 60
    world_str = "{:02d}:{:02d} {}".format(world_hours, world_minutes, tz_names[tz_index])
    utc_label.text = world_str

while True:
    elapsed = time.monotonic() - start_mono
    total_seconds = (initial_hours * 3600 + initial_minutes * 60 + initial_seconds) + elapsed
    local_hours = int(total_seconds // 3600) % 24
    local_minutes = int(total_seconds // 60) % 60
    local_seconds = total_seconds % 60
    utc_hours = int((total_seconds + 8 * 3600) // 3600) % 24
    utc_minutes = int((total_seconds + 8 * 3600) // 60) % 60
    utc_seconds = (total_seconds + 8 * 3600) % 60
    local_str = "{:02d}:{:02d}:{:02d}".format(local_hours, local_minutes, int(local_seconds))
    utc_str = "{:02d}:{:02d}:{:02d}".format(utc_hours, utc_minutes, int(utc_seconds))
    local_label.text = local_str
    sec_in_minute = int(local_seconds) % 60

    if not button_up.value:
        mode = (mode + 1) % 4
        time.sleep(0.2)
    if not button_down.value:
        if mode == 0:
            ft8_tx_mode = 1 - ft8_tx_mode
        elif mode == 2:
            settings_tz = (settings_tz + 1) % 3
        elif mode == 3:
            world_tz = (world_tz + 1) % 3
        time.sleep(0.2)

    if mode == 0:
        display_ft8(local_str, utc_str, sec_in_minute, ft8_tx_mode)
    elif mode == 1:
        display_general(local_str, utc_str, sec_in_minute)
    elif mode == 2:
        display_settings(settings_tz)
    elif mode == 3:
        display_world(local_str, total_seconds, world_tz)

    if time.monotonic() - last_drift_check >= 300 and network:
        ntp_time = fetch_time()
        if ntp_time is not None:
            ntp_hours, ntp_minutes, ntp_seconds = ntp_time
            local_total = local_hours * 3600 + local_minutes * 60 + local_seconds
            ntp_total = ntp_hours * 3600 + ntp_minutes * 60 + ntp_seconds
            if ntp_hours < local_hours and time.monotonic() - last_sync > 43200:
                ntp_total += 86400
            drift = ntp_total - local_total
            dot_pos = max(0, min(63, 32 + int(drift * 10)))
            drift_sprite.x = dot_pos
            if abs(drift) > drift_threshold:
                elapsed_since_sync = time.monotonic() - last_sync
                drift_rate = abs(drift) / elapsed_since_sync
                new_interval = int(drift_threshold / drift_rate)
                sync_interval = max(300, min(new_interval, 86400))
                save_sync_interval(sync_interval)
                initial_hours, initial_minutes, initial_seconds = ntp_time
                start_mono = time.monotonic()
                last_sync = start_mono
            last_drift_check = time.monotonic()

    display.show(group)
    time.sleep(1)