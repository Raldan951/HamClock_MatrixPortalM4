# Import modules for a basic internet clock display
import board
import time
import neopixel
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network  # For WiFi and NTP time fetching
import terminalio
from adafruit_display_text import label

# Setup NeoPixel for status feedback
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)  # Single NeoPixel on the board
pixel[0] = (255, 0, 0)  # Red: Code is starting
time.sleep(2)  # Pause to see the red light

# Release any existing display resources
pixel[0] = (255, 255, 0)  # Yellow: Clearing prior displays
displayio.release_displays()  # Free up display memory
time.sleep(1)  # Short delay to settle

# Setup the matrix display
pixel[0] = (0, 255, 0)  # Green: Initializing matrix
matrix = Matrix(width=64, height=32, bit_depth=1)  # 64x32 matrix, 1-bit color depth
display = matrix.display  # Get the display object for rendering
time.sleep(1)  # Let matrix stabilize

# Setup network connection for internet time
pixel[0] = (128, 0, 128)  # Purple: Connecting to WiFi
network = Network(status_neopixel=board.NEOPIXEL, debug=False)  # Use secrets.py for WiFi creds
time.sleep(1)  # Wait for network to connect

# Create a label for the clock display
clock_label = label.Label(
    terminalio.FONT,  # Built-in font for simplicity
    text="00:00:00",  # Placeholder for HH:MM:SS
    color=0x00FF00,  # Green text to start
    x=0, y=16  # Left-aligned, vertically centered on 32-pixel height
)
group = displayio.Group()  # Group to hold display elements
group.append(clock_label)  # Add clock text to group
display.show(group)  # Render the group on the matrix

pixel[0] = (0, 255, 0)  # Green: Clock is running
while True:  # Loop forever to update time
    # Fetch current time from Adafruit IO’s NTP service
    current_time = network.get_local_time()  # Returns a time struct (adjusted for timezone via IO)
    # Format time as HH:MM:SS (24-hour format)
    time_str = "{:02d}:{:02d}:{:02d}".format(
        current_time.tm_hour,
        current_time.tm_min,
        current_time.tm_sec
    )
    clock_label.text = time_str  # Update the displayed time
    time.sleep(1)  # Refresh every second