# HamClockV1.3: FT8, General, Settings Modes with Buttons
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

matrix = Matrix(width=64, height=32, bit_depth=1)
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
    """Fetch current time from Adafruit IO NTP service with fractional seconds."""
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

local_label = label.Label(terminalio.FONT, text="00:00:00", color=0x00FF00, x=4, y=8)
utc_label = label.Label(terminalio.FONT, text="00:00:00", color=0xFFFF00, x=4, y=24)
line_palette = Palette(2)
line_palette[0] = 0x000000
line_palette[1] = 0x00FF00
line_bitmap = Bitmap(64, 2, 1)
for x in range(64):
    line_bitmap[x, 0] = 1
    line_bitmap[x, 1] = 1
line_sprite = displayio.TileGrid(line_bitmap, pixel_shader=line_palette, x=0, y=15)
drift_palette = Palette(2)
drift_palette[0] = 0x000000
drift_palette[1] = 0x0000FF
drift_bitmap = Bitmap(1, 2, 1)
drift_bitmap[0, 0] = 1
drift_bitmap[0, 1] = 1
drift_sprite = displayio.TileGrid(drift_bitmap, pixel_shader=drift_palette, x=32, y=15)
dot_palette = Palette(2)
dot_palette[0] = 0x000000
dot_palette[1] = 0x00FF00
dot_bitmap = Bitmap(1, 1, 1)
dot_bitmap[0, 0] = 1
dot_above = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=14)
dot_below = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=17)
tx_blue_palette = Palette(2)
tx_blue_palette[0] = 0x000000
tx_blue_palette[1] = 0x0000FF
tx_blue_bitmap = Bitmap(9, 15, 1)
for y in range(2):
    for x in range(9): tx_blue_bitmap[x, y] = 1
tx_blue_bitmap[0, 2] = 1; tx_blue_bitmap[1, 2] = 1; tx_blue_bitmap[7, 2] = 1; tx_blue_bitmap[8, 2] = 1
for y in range(3, 7):
    tx_blue_bitmap[0, y] = 1; tx_blue_bitmap[1, y] = 1; tx_blue_bitmap[2, y] = 1; tx_blue_bitmap[3, y] = 1
    tx_blue_bitmap[5, y] = 1; tx_blue_bitmap[6, y] = 1; tx_blue_bitmap[7, y] = 1; tx_blue_bitmap[8, y] = 1
for x in range(9): tx_blue_bitmap[x, 7] = 1
tx_blue_bitmap[0, 8] = 1; tx_blue_bitmap[1, 8] = 1; tx_blue_bitmap[3, 8] = 1; tx_blue_bitmap[4, 8] = 1
tx_blue_bitmap[5, 8] = 1; tx_blue_bitmap[7, 8] = 1; tx_blue_bitmap[8, 8] = 1
tx_blue_bitmap[0, 9] = 1; tx_blue_bitmap[1, 9] = 1; tx_blue_bitmap[2, 9] = 1
tx_blue_bitmap[4, 9] = 1; tx_blue_bitmap[6, 9] = 1; tx_blue_bitmap[7, 9] = 1; tx_blue_bitmap[8, 9] = 1
tx_blue_bitmap[0, 10] = 1; tx_blue_bitmap[1, 10] = 1; tx_blue_bitmap[2, 10] = 1; tx_blue_bitmap[3, 10] = 1
tx_blue_bitmap[5, 10] = 1; tx_blue_bitmap[6, 10] = 1; tx_blue_bitmap[7, 10] = 1; tx_blue_bitmap[8, 10] = 1
tx_blue_bitmap[0, 11] = 1; tx_blue_bitmap[1, 11] = 1; tx_blue_bitmap[2, 11] = 1
tx_blue_bitmap[4, 11] = 1; tx_blue_bitmap[6, 11] = 1; tx_blue_bitmap[7, 11] = 1; tx_blue_bitmap[8, 11] = 1
tx_blue_bitmap[0, 12] = 1; tx_blue_bitmap[1, 12] = 1; tx_blue_bitmap[3, 12] = 1; tx_blue_bitmap[4, 12] = 1
tx_blue_bitmap[5, 12] = 1; tx_blue_bitmap[7, 12] = 1; tx_blue_bitmap[8, 12] = 1
for y in range(13, 15):
    for x in range(9): tx_blue_bitmap[x, y] = 1
tx_blue_sprite = displayio.TileGrid(tx_blue_bitmap, pixel_shader=tx_blue_palette, x=55, y=0)
tx_white_palette = Palette(2)
tx_white_palette[0] = 0x0000FF
tx_white_palette[1] = 0xFFFFFF
tx_white_bitmap = Bitmap(9, 15, 1)
tx_white_bitmap[2, 2] = 1; tx_white_bitmap[3, 2] = 1; tx_white_bitmap[4, 2] = 1; tx_white_bitmap[5, 2] = 1; tx_white_bitmap[6, 2] = 1
for y in range(3, 7): tx_white_bitmap[4, y] = 1
tx_white_bitmap[2, 8] = 1; tx_white_bitmap[6, 8] = 1
tx_white_bitmap[3, 9] = 1; tx_white_bitmap[5, 9] = 1
tx_white_bitmap[4, 10] = 1
tx_white_bitmap[3, 11] = 1; tx_white_bitmap[5, 11] = 1
tx_white_bitmap[2, 12] = 1; tx_white_bitmap[6, 12] = 1
tx_white_sprite = displayio.TileGrid(tx_white_bitmap, pixel_shader=tx_white_palette, x=55, y=0)
settings_label = label.Label(terminalio.FONT, text="PST", color=0xFFFFFF, x=20, y=16)

group = displayio.Group()
mode = 0  # 0: FT8, 1: General, 2: Settings
ft8_tx_mode = 0  # 0: Even, 1: Odd
settings_tz = 0  # 0: PST, 1: UTC, 2: EST

def display_ft8(local_str, utc_str, sec_in_minute, tx_mode):
    while len(group) > 0:  # Clear group
        group.pop()
    group.append(local_label)
    group.append(utc_label)
    group.append(line_sprite)
    group.append(drift_sprite)
    group.append(dot_above)
    group.append(dot_below)
    group.append(tx_blue_sprite)
    group.append(tx_white_sprite)
    tx_white_palette[0] = 0xFF0000 if tx_mode == 0 else 0x0000FF
    if tx_mode == 0:
        tx_blue_sprite.y = tx_white_sprite.y = 0 if (0 <= sec_in_minute <= 14 or 30 <= sec_in_minute <= 44) else 17
    else:
        tx_blue_sprite.y = tx_white_sprite.y = 0 if (15 <= sec_in_minute <= 29 or 45 <= sec_in_minute <= 59) else 17

def display_general(local_str, utc_str, sec_in_minute):
    while len(group) > 0:
        group.pop()
    group.append(local_label)
    group.append(line_sprite)
    group.append(drift_sprite)
    group.append(dot_above)
    group.append(dot_below)
    group.append(utc_label)
    local_label.x = 8
    utc_label.x = 8
    local_label.y = 8
    utc_label.y = 24

def display_settings(tz_index):
    while len(group) > 0:
        group.pop()
    group.append(settings_label)
    tz_names = ["PST", "UTC", "EST"]
    settings_label.text = tz_names[tz_index]

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
    utc_label.text = utc_str
    sec_in_minute = int(local_seconds) % 60

    if not button_up.value:
        mode = (mode + 1) % 3
        time.sleep(0.2)
    if not button_down.value:
        if mode == 0:
            ft8_tx_mode = 1 - ft8_tx_mode
        elif mode == 2:
            settings_tz = (settings_tz + 1) % 3
        time.sleep(0.2)

    if mode == 0:
        display_ft8(local_str, utc_str, sec_in_minute, ft8_tx_mode)
    elif mode == 1:
        display_general(local_str, utc_str, sec_in_minute)
    elif mode == 2:
        display_settings(settings_tz)

    if time.monotonic() - last_drift_check >= 300 and network:
        ntp_time = fetch_time()
        if ntp_time is not None:
            initial_hours, initial_minutes, initial_seconds = ntp_time
            start_mono = time.monotonic()
            last_sync = start_mono
        last_drift_check = time.monotonic()

    display.show(group)
    time.sleep(1)