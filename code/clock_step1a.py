# Import modules for a dual-time clock with drift indicator
import board
import time
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import terminalio
from adafruit_display_text import label
import os
from displayio import Palette, Bitmap

# Release any existing display resources
displayio.release_displays()
time.sleep(1)

# Setup the matrix display
matrix = Matrix(width=64, height=32, bit_depth=1)
display = matrix.display
time.sleep(1)

# Setup network connection
network = Network(status_neopixel=board.NEOPIXEL, debug=True)
time.sleep(5)

def fetch_time():
    """Fetch time from Adafruit IO, return hours, minutes, seconds (local)."""
    try:
        current_time = network.get_local_time()
        if isinstance(current_time, str):
            time_parts = current_time.split(" ")
            time_str = time_parts[1].split(".")[0]
            hours, minutes, seconds = map(int, time_str.split(":"))
            return hours, minutes, seconds
        else:
            return current_time.tm_hour, current_time.tm_min, current_time.tm_sec
    except Exception:
        return None

def load_sync_interval():
    """Load saved sync interval, default to 3600."""
    try:
        with open("/sync_interval.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 3600

def save_sync_interval(interval):
    """Save sync interval to file."""
    try:
        with open("/sync_interval.txt", "w") as f:
            f.write(str(interval))
    except:
        pass

# Initial time fetch (local PST)
hours, minutes, seconds = fetch_time() or (0, 0, 0)
start_mono = time.monotonic()
last_sync = start_mono
sync_interval = load_sync_interval()
last_drift_check = start_mono
drift_threshold = 1

# Create labels for local (top) and UTC (bottom), centered
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

# Create green line (1 pixel tall)
line_palette = Palette(1)
line_palette[0] = 0x00FF00  # Green
line_bitmap = Bitmap(64, 1, 1)
for x in range(64):
    line_bitmap[x, 0] = 0  # Full green line
line_sprite = displayio.TileGrid(line_bitmap, pixel_shader=line_palette, x=0, y=16)

# Create blue drift dot
drift_palette = Palette(2)
drift_palette[0] = 0x000000  # Transparent
drift_palette[1] = 0x0000FF  # Blue
drift_bitmap = Bitmap(1, 1, 1)
drift_bitmap[0, 0] = 1  # Single blue pixel
drift_sprite = displayio.TileGrid(drift_bitmap, pixel_shader=drift_palette, x=32, y=16)

# Create green marker dots (above and below)
dot_palette = Palette(2)
dot_palette[0] = 0x000000  # Transparent
dot_palette[1] = 0x00FF00  # Full green
dot_bitmap = Bitmap(1, 1, 1)
dot_bitmap[0, 0] = 1  # Single green pixel
dot_above = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=15)
dot_below = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette, x=32, y=17)

# Setup display group
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
    # Calculate elapsed seconds
    elapsed = int(time.monotonic() - start_mono)
    total_seconds = seconds + elapsed
    local_hours = (hours + (total_seconds // 3600)) % 24
    local_minutes = (minutes + (total_seconds // 60)) % 60
    local_seconds = total_seconds % 60
    utc_hours = (local_hours + 8) % 24
    utc_minutes = local_minutes
    utc_seconds = local_seconds
    # Update displays
    local_str = "{:02d}:{:02d}:{:02d}".format(local_hours, local_minutes, local_seconds)
    utc_str = "{:02d}:{:02d}:{:02d}".format(utc_hours, utc_minutes, utc_seconds)
    local_label.text = local_str
    utc_label.text = utc_str

    # Check drift every 5 minutes
    if time.monotonic() - last_drift_check >= 300:
        ntp_time = fetch_time()
        if ntp_time:
            ntp_hours, ntp_minutes, ntp_seconds = ntp_time
            local_total = local_hours * 3600 + local_minutes * 60 + local_seconds
            ntp_total = ntp_hours * 3600 + ntp_minutes * 60 + ntp_seconds
            if ntp_hours < local_hours and time.monotonic() - last_sync > 43200:
                ntp_total += 86400
            drift = ntp_total - local_total
            dot_pos = max(0, min(63, 32 + int(drift * 10)))  # 1 pixel = 0.1s drift
            drift_sprite.x = dot_pos  # Move blue dot
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

    # Resync if interval elapsed
    if time.monotonic() - last_sync >= sync_interval:
        sync_time = fetch_time()
        if sync_time:
            hours, minutes, seconds = sync_time
            start_mono = time.monotonic()
            last_sync = start_mono

    display.show(group)
    time.sleep(1)  # 1-second updates