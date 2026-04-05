import asyncio
import struct
from bleak import BleakScanner, BleakClient

import matplotlib.pyplot as plt
#import numpy as np

LOGGER_DURATION = 30

#// BLE Characteristics
#define SAMPLE_DATA_SERV "99b3357d-3edf-4dfd-a6de-7a409c0be76b"
#define SAMPLE_DATA_UUID "20c03e1b-a755-4882-baad-5eaa29e1ce70"
#define SAMPLE_MSEC_UUID "20c03e1b-a755-4882-baad-5eaa29e1ce71"
#define SAMPLE_CHAN_UUID "20c03e1b-a755-4882-baad-5eaa29e1ce72"

SAMPLE_DATA_SERV  = "99b3357d-3edf-4dfd-a6de-7a409c0be76b"
SAMPLE_DATA_UUID = "20c03e1b-a755-4882-baad-5eaa29e1ce70"
SAMPLE_MSEC_UUID = "20c03e1b-a755-4882-baad-5eaa29e1ce71"
SAMPLE_CHAN_UUID = "20c03e1b-a755-4882-baad-5eaa29e1ce72"


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
        
        await asyncio.sleep(0.5)  # Give ESP32 time to settle
        
        char = client.services.get_characteristic(SAMPLE_MSEC_UUID)
        print(f"Char properties: {char.properties}")

        '''
        # Dump everything Bleak sees
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Char: {char.uuid}  Properties: {char.properties}")
         '''
         
        # Write sample interval in milliseconds.  Little Endian unsigned long (L).
        sample_msec = 500 # 250;
        data = struct.pack('<I', sample_msec)
        await client.write_gatt_char(SAMPLE_MSEC_UUID, data, response=True)
        print(f'msec: {sample_msec}')
        
        # Write data source (e.g., source 1 as uint8)
        sample_chan = 1
        data = struct.pack('<B', sample_chan)
        await client.write_gatt_char(SAMPLE_CHAN_UUID, data, response=True)
        print(f'Chan: {sample_chan}')
        
        # 3. Subscribe to notifications
        print('Starting...')
        await client.start_notify(SAMPLE_DATA_UUID, notification_handler)
        print('Started.')
        # 4. Keep running to receive data
        await asyncio.sleep(LOGGER_DURATION)

        await client.stop_notify(SAMPLE_DATA_UUID)

asyncio.run(main())

print(f'{len(samples)} samples')

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

