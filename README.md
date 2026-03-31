# BLE Logger Notify

This implements a data logger that communicates with its client application via Bluetooth Low Energy (BLE).

## Arduino ESP32-C3

### BLE Library
The Arduino code uses the NimBLE-Arduino by h2zero.  The UUIDs were made up using [uuidgenerator](https://www.uuidgenerator.net/).

### Hardware
The initial hardware was the M5Stack **M5Stamp C3U Mate** although I migrated to an Aliexpress **ESP32-C3 SuperMini** for no particular reason other than to see if it would work as well.  It does.

```
// NOTE: The M5StampC3:  button on GPIO0, LED on GPIO21.
//       The M5StampC3U: button on GPIO9, LED on GPIO2
//       The ESP32C3 SuperMini: button on GPIO9, LED on GPIO8.
```

Apparently the ESP32-C3 has a disappointing ADC.  There is an offset as well as non-linearities. It is definitely usable if your need for accuracy isn't high.  It looks like the ESP32-C5 is an improvement. 

## Client
### BLE Library
The client software uses the Bleak.  It was tested on Linux Mint. In this version, it collects 30 seconds of data and then plots it.

## To Do List
* Add configuration for sample rate and data sources.
* Do live plotting.
* Save the data.
* Port to a device with a better ADC.





