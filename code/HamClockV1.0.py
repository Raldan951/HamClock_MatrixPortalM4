# Ham Radio Clock: Displays local (PST) and UTC times with a drift indicator
# - Local time on top (green), centered
# - Green line (y=16) with green dots above (y=15) and below (y=17) at x=32
# - Blue drift dot moves on the line (1 pixel = 0.1s drift)
# - UTC time on bottom (yellow), centered
# - Syncs with Adafruit IO NTP, adjusts drift every 5min, saves sync interval
# Created by Pete Parise with Grok 3 by xAI, Feb 22, 2025
# Updated Feb 23, 2025: Fractional drift precision, whole-second display

import board
import time  # For sleep and monotonic timing
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
    """Fetch current time from Adafruit IO NTP service with fractional seconds.
    Returns: tuple (hours, minutes, seconds) where seconds includes decimals."""
    try:
        current_time = network.get_local_time()  # "YYYY-MM-DD HH:MM:SS.mmm ..."
        if isinstance(current_time, str):
            time_parts = current_time.split(" ")
            time_str = time_parts[1]  # "HH:MM:SS.mmm"
            hours, minutes, seconds_ms = time_str.split(":")
            seconds, ms = seconds_ms.split(".")  # Split "SS.mmm"
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(ms) / 1000
            return (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
        else:
            return current_time.tm_hour, current_time.tm_min, current_time.tm_sec
    except Exception:
        return None

def load_sync_interval():
    """Load the last saved sync interval from file.
    Returns: integer (seconds), defaults to 3600 (1 hour) if file missing."""
    try:
        with open("/sync_interval.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 3600

def save_sync_interval(interval):
    """Save the calculated sync interval to file for persistence."""
    try:
        with open("/sync_interval.txt", "w") as f:
            f.write(str(interval))
    except:
        pass

hours, minutes, seconds = fetch_time() or (0, 0, 0)
start_mono = time.monotonic()
last_sync = start_mono
sync_interval = load_sync_interval()
last_drift_check = start_mono
drift_threshold = 1

local_label = label.Label(
    terminalio.FONT,
    text="00:00:00",
    color=0x00FF00,
    x=8, y=8
)
utc_label = label.Label(
    terminalio.FONT,
    text="00:00:00",
    color=0xFFFF00,
    x=8, y=24
)

line_palette = Palette(1)
line_palette[0] = 0x00FF00
line_bitmap = Bitmap(64, 1, 1)
for x in range(64):
    line_bitmap[x, 0] = 0
line_sprite = displayio.TileGrid(line_bitmap, pixel_shader=line_palette, x=0, y=16)

drift_palette = Palette(2)
drift_palette[0] = 0x000000
drift_palette[1] = 0x0000FF
drift_bitmap = Bitmap(1, 1, 1)
drift_bitmap[0, 0] = 1
drift_sprite = displayio.TileGrid(drift_bitmap, pixel_shader=drift_palette, x=32, y=16)

dot_palette = Palette(2)
dot_palette[0] = 0x000000
dot_palette[1] = 0x00FF00
dot_bitmap = Bitmap(1, 1, 1)
dot_bitmap[0, 0] = 1
dot_above = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=15)
dot_below = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=17)

group = displayio.Group()
group.append(local_label)
group.append(line_sprite)
group.append(dot_above)
group.append(dot_below)
group.append(drift_sprite)
group.append(utc_label)
try:
    display.show(group)
except Exception as e:
    with open("/error.txt", "w") as f:
        f.write("Display Error: {}\n".format(str(e)))

while True:
    elapsed = time.monotonic() - start_mono
    total_seconds = seconds + elapsed
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

    if time.monotonic() - last_drift_check >= 300:
        ntp_time = fetch_time()
        if ntp_time:
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
                hours, minutes, seconds = ntp_time
                start_mono = time.monotonic()
                last_sync = start_mono
            last_drift_check = time.monotonic()

    if time.monotonic() - last_sync >= sync_interval:
        sync_time = fetch_time()
        if sync_time:
            hours, minutes, seconds = sync_time
            start_mono = time.monotonic()
            last_sync = start_mono

    display.show(group)
    time.sleep(1)