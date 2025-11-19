# Ham Radio Clock V1.2: Displays local (PST) and UTC times with FT8 TX indicator
# - Local time on top (green), shifted left (x=4)
# - Green line (y=15-16, 2px tall) with green dot above (y=14) and below (y=16) at x=32
# - Blue drift dot (2px tall, y=15-16) moves on the line (1 pixel = 0.1s drift)
# - UTC time on bottom (yellow), shifted left (x=4)
# - "TX" box (blue X's, white O's via layers, 9x15) on right: top (0-14s, 30-44s), bottom (15-29s, 45-59s)
# - Syncs with Adafruit IO NTP every 5min, saves sync interval
# Created by Pete Parise and Grok 3 (xAI), Feb 22-23, 2025

import board
import time
import displayio
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
time.sleep(1)

network = Network(status_neopixel=board.NEOPIXEL, debug=True)
time.sleep(5)

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

ntp_time = fetch_time()
if ntp_time is not None:
    initial_hours, initial_minutes, initial_seconds = ntp_time
    print("Initial sync:", (initial_hours, initial_minutes, initial_seconds))
else:
    initial_hours, initial_minutes, initial_seconds = (0, 0, 0)
    print("Initial fetch failed, using 0:0:0")
start_mono = time.monotonic()
last_sync = start_mono
sync_interval = load_sync_interval()
last_drift_check = start_mono
drift_threshold = 1

local_label = label.Label(
    terminalio.FONT,
    text="00:00:00",
    color=0x00FF00,
    x=4, y=8
)
utc_label = label.Label(
    terminalio.FONT,
    text="00:00:00",
    color=0xFFFF00,
    x=4, y=24
)

line_palette = Palette(2)
line_palette[0] = 0x000000
line_palette[1] = 0x00FF00
line_bitmap = Bitmap(64, 2, 1)  # 2px tall
for x in range(64):
    line_bitmap[x, 0] = 1  # y=15
    line_bitmap[x, 1] = 1  # y=16
line_sprite = displayio.TileGrid(line_bitmap, pixel_shader=line_palette, x=0, y=15)  # Shifted up

drift_palette = Palette(2)
drift_palette[0] = 0x000000
drift_palette[1] = 0x0000FF
drift_bitmap = Bitmap(1, 2, 1)  # 2px tall
drift_bitmap[0, 0] = 1  # y=15
drift_bitmap[0, 1] = 1  # y=16
drift_sprite = displayio.TileGrid(drift_bitmap, pixel_shader=drift_palette, x=32, y=15)  # Shifted up

dot_palette = Palette(2)
dot_palette[0] = 0x000000
dot_palette[1] = 0x00FF00
dot_bitmap = Bitmap(1, 1, 1)
dot_bitmap[0, 0] = 1
dot_above = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=14)  # Shifted up
dot_below = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=17)  # Not Shifted up

# TX Indicator: 9x15 box (blue X's layer)
tx_blue_palette = Palette(2)
tx_blue_palette[0] = 0x000000  # Black
tx_blue_palette[1] = 0x0000FF  # Blue
tx_blue_bitmap = Bitmap(9, 15, 1)
for y in range(2):
    for x in range(9): tx_blue_bitmap[x, y] = 1  # Row 0-1: XXXXXXXXX
tx_blue_bitmap[0, 2] = 1; tx_blue_bitmap[1, 2] = 1; tx_blue_bitmap[7, 2] = 1; tx_blue_bitmap[8, 2] = 1  # Row 2: XXOOOOOXX
for y in range(3, 7):
    tx_blue_bitmap[0, y] = 1; tx_blue_bitmap[1, y] = 1; tx_blue_bitmap[2, y] = 1; tx_blue_bitmap[3, y] = 1  # Row 3-6: XXXXOXXXX
    tx_blue_bitmap[5, y] = 1; tx_blue_bitmap[6, y] = 1; tx_blue_bitmap[7, y] = 1; tx_blue_bitmap[8, y] = 1
for x in range(9): tx_blue_bitmap[x, 7] = 1  # Row 7: XXXXXXXXX
tx_blue_bitmap[0, 8] = 1; tx_blue_bitmap[1, 8] = 1; tx_blue_bitmap[3, 8] = 1; tx_blue_bitmap[4, 8] = 1  # Row 8: XXOXXXOXX
tx_blue_bitmap[5, 8] = 1; tx_blue_bitmap[7, 8] = 1; tx_blue_bitmap[8, 8] = 1
tx_blue_bitmap[0, 9] = 1; tx_blue_bitmap[1, 9] = 1; tx_blue_bitmap[2, 9] = 1  # Row 9: XXXOXOXXX
tx_blue_bitmap[4, 9] = 1; tx_blue_bitmap[6, 9] = 1; tx_blue_bitmap[7, 9] = 1; tx_blue_bitmap[8, 9] = 1
tx_blue_bitmap[0, 10] = 1; tx_blue_bitmap[1, 10] = 1; tx_blue_bitmap[2, 10] = 1; tx_blue_bitmap[3, 10] = 1  # Row 10: XXXXOXXXX
tx_blue_bitmap[5, 10] = 1; tx_blue_bitmap[6, 10] = 1; tx_blue_bitmap[7, 10] = 1; tx_blue_bitmap[8, 10] = 1
tx_blue_bitmap[0, 11] = 1; tx_blue_bitmap[1, 11] = 1; tx_blue_bitmap[2, 11] = 1  # Row 11: XXXOXOXXX
tx_blue_bitmap[4, 11] = 1; tx_blue_bitmap[6, 11] = 1; tx_blue_bitmap[7, 11] = 1; tx_blue_bitmap[8, 11] = 1
tx_blue_bitmap[0, 12] = 1; tx_blue_bitmap[1, 12] = 1; tx_blue_bitmap[3, 12] = 1; tx_blue_bitmap[4, 12] = 1  # Row 12: XXOXXXOXX
tx_blue_bitmap[5, 12] = 1; tx_blue_bitmap[7, 12] = 1; tx_blue_bitmap[8, 12] = 1
for y in range(13, 15):
    for x in range(9): tx_blue_bitmap[x, y] = 1  # Row 13-14: XXXXXXXXX
tx_blue_sprite = displayio.TileGrid(tx_blue_bitmap, pixel_shader=tx_blue_palette, x=55, y=0)

# White O's layer
tx_white_palette = Palette(2)
tx_white_palette[0] = 0x0000FF  # Blue (your tweak)
tx_white_palette[1] = 0xFFFFFF  # White
tx_white_bitmap = Bitmap(9, 15, 1)
tx_white_bitmap[2, 2] = 1; tx_white_bitmap[3, 2] = 1; tx_white_bitmap[4, 2] = 1; tx_white_bitmap[5, 2] = 1; tx_white_bitmap[6, 2] = 1  # Row 2: XXOOOOOXX
for y in range(3, 7): tx_white_bitmap[4, y] = 1  # Row 3-6: XXXXOXXXX
tx_white_bitmap[2, 8] = 1; tx_white_bitmap[6, 8] = 1  # Row 8: XXOXXXOXX
tx_white_bitmap[3, 9] = 1; tx_white_bitmap[5, 9] = 1  # Row 9: XXXOXOXXX
tx_white_bitmap[4, 10] = 1  # Row 10: XXXXOXXXX
tx_white_bitmap[3, 11] = 1; tx_white_bitmap[5, 11] = 1  # Row 11: XXXOXOXXX
tx_white_bitmap[2, 12] = 1; tx_white_bitmap[6, 12] = 1  # Row 12: XXOXXXOXX
tx_white_sprite = displayio.TileGrid(tx_white_bitmap, pixel_shader=tx_white_palette, x=55, y=0)

group = displayio.Group()
group.append(local_label)
group.append(line_sprite)
group.append(dot_above)
group.append(dot_below)
group.append(drift_sprite)
group.append(tx_blue_sprite)
group.append(tx_white_sprite)
group.append(utc_label)
try:
    display.show(group)
except Exception as e:
    with open("/error.txt", "w") as f:
        f.write("Display Error: {}\n".format(str(e)))

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
    if (0 <= sec_in_minute <= 14) or (30 <= sec_in_minute <= 44):
        tx_blue_sprite.y = 0
        tx_white_sprite.y = 0
    else:
        tx_blue_sprite.y = 17
        tx_white_sprite.y = 17

    if time.monotonic() - last_drift_check >= 300:
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

    if time.monotonic() - last_sync >= sync_interval:
        sync_time = fetch_time()
        if sync_time is not None:
            initial_hours, initial_minutes, initial_seconds = sync_time
            start_mono = time.monotonic()
            last_sync = start_mono

    display.show(group)
    time.sleep(1)