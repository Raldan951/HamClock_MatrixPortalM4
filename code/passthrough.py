# Passthrough code to bridge SAMD51 USB to ESP32-S2 serial for firmware flashing
import board
import busio
from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi as adafruit_espspi
import time  # For sleep functionality
import sys   # Added for stdin/stdout

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI Passthrough")

# Set up SPI pins to communicate with ESP32-S2
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_espspi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Reset ESP32-S2 into bootloader mode
esp32_reset.value = False  # Pull reset LOW
time.sleep(0.01)  # Short delay
esp32_reset.value = True  # Release reset
time.sleep(0.5)  # Wait for bootloader

# Bridge USB to ESP32-S2 serial
while True:
    try:
        b = sys.stdin.buffer.read(1)
        if b == None:
            continue
        esp.write(b)
    except:
        pass

    try:
        numbytes = esp.unread_length
        if numbytes > 0:
            b = esp.read(numbytes)
            sys.stdout.buffer.write(b)
            sys.stdout.buffer.flush()
    except:
        pass