import asyncio
from bleak import BleakScanner, BleakClient

import matplotlib.pyplot as plt
#import numpy as np

LOGGER_DURATION = 30

SERVICE_UUID  = "99b3357d-3edf-4dfd-a6de-7a409c0be76b"
CHAR_UUID     = "20c03e1b-a755-4882-baad-5eaa29e1ce73"

samples = []

# Callback — fires every time ESP32 calls notify()
def notification_handler(sender, data: bytearray):
    global samples
    # String Data:
    #print(f"Received: {data.decode('utf-8')} {len(data)}")
    
    # Byte Array:
    #hex_string = data.hex(' ')
    #print(hex_string)
    
    # 16-bit, little endian:
    values = [int.from_bytes(data[i:i+2], 'little', signed=False) for i in range(0, len(data), 2)]
    print(f"Data: {values}")
    samples += values
    
    # Parse and log data here

async def main():
    # 1. Scan for the device
    device = await BleakScanner.find_device_by_name("ESP32-DataLogger", timeout=30.0)
    
    
    if device is None:
        print("Device not found. Is it advertising?")
        return
    else:
        print('Found')
        print(str(device))

    # 2. Connect (required for GATT/Notifications)
    async with BleakClient(device) as client:
        
        # 3. Subscribe to notifications
        print('Starting...')
        await client.start_notify(CHAR_UUID, notification_handler)
        print('Started.')
        # 4. Keep running to receive data
        await asyncio.sleep(LOGGER_DURATION)

        await client.stop_notify(CHAR_UUID)

asyncio.run(main())

x = [None] * len(samples)
value = 0
for ii in range(0, len(samples)):
    x[ii] = value
    value += 0.5
    
plt.plot(x, samples)
plt.title("Matplotlib Plot in a GUI Window")
plt.xlabel("X axis")
plt.ylabel("Y axis")
plt.ylim(0, 4095)
plt.show() # This opens a local window

'''

**Key receive functions:**
| Function | Purpose |
|---|---|
| `BleakScanner.find_device_by_name()` | Scan and find the ESP32 by name |
| `BleakScanner.discover()` | Scan and list all nearby BLE devices |
| `BleakClient(device)` | Create a connection to the peripheral |
| `client.start_notify(uuid, callback)` | **Subscribe to notifications — main receive function** |
| `client.read_gatt_char(uuid)` | Poll/read a value on demand (no notification needed) |
| `client.stop_notify(uuid)` | Unsubscribe from notifications |

---

### Recommended Architecture for Data Logging
'''

'''
ESP32-C3                          Python / Bleak
──────────────────                ─────────────────────────
advertise()          ──scan──>    BleakScanner.find_device()
                     <─connect─   BleakClient.connect()
                     <─subscribe─ client.start_notify()
notify(data)         ──data──>    notification_handler(data)
notify(data)         ──data──>    → write to CSV / database
...continuously...
'''

