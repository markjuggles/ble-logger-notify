/*
 * Program: BLE Logger Notify
 * Purpose: Send data to the client app via notifications.
 * v1: Constant Data
 */

#include <NimBLEDevice.h>
#include <Arduino.h>
#include <FastLED.h>

#define PIN_BUTTON  9
#define NUM_LEDS    1
#define DATA_PIN    8

// LED Globals
CRGB leds[NUM_LEDS];
int  loopCount = 0;

// ADC Globals and callback.
#define NSAMPLES  4
hw_timer_t* timer = NULL;

volatile uint16_t adcBuffer[2][NSAMPLES];
volatile uint8_t  adcIndex = 0;
volatile uint8_t  adcBufNum = 0;
volatile bool adcBuf0Full = false;
volatile bool adcBuf1Full = false;
volatile bool adcOverrun = false;

void ARDUINO_ISR_ATTR onTimer()
{
  // Grab the current sample first thing to provide more consistent timing.
  volatile uint16_t adcValue = analogRead(A1);      // or the GPIO you use
  adcValue += analogRead(A1);

  if(adcIndex >= NSAMPLES)
  {
    // Mark the current buffer as full.
    if(adcBufNum == 0) adcBuf0Full = true;
    if(adcBufNum == 1) adcBuf1Full = true;

    // Toggle buffer, check for data overrun, restart the index.
    adcBufNum ^= 1;
    if((adcBufNum == 0) && adcBuf0Full) adcOverrun = true;
    if((adcBufNum == 1) && adcBuf1Full) adcOverrun = true;
    adcIndex = 0;
  }

  // Save the sample.
  adcBuffer[adcBufNum][adcIndex++] = adcValue/2;
}

NimBLEServer* pServer;
NimBLECharacteristic* pDataChar;

// ServerCallbacks
// We need to catch the disconnect to reenable advertising so that it 
// will work more than one time.
class ServerCallbacks : public NimBLEServerCallbacks
{
public:
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override
    {
        Serial.println("Client connected");
    }

    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override
    {
        Serial.println("Client disconnected - restarting advertising");
        NimBLEDevice::getAdvertising()->start();
    }
};


ServerCallbacks serverCallbacks;


void setup()
{
    Serial.begin(9600);
    NimBLEDevice::init("ESP32-DataLogger");
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(&serverCallbacks);

    NimBLEService* pService = pServer->createService("99b3357d-3edf-4dfd-a6de-7a409c0be76b");
    pDataChar = pService->createCharacteristic(
        "20c03e1b-a755-4882-baad-5eaa29e1ce73",
        NIMBLE_PROPERTY::READ |
        NIMBLE_PROPERTY::NOTIFY
    );
    pService->start();

    // Configure advertising ONCE, THEN start
    NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();

    NimBLEAdvertisementData advData;
    advData.setName("ESP32-DataLogger");
    advData.addServiceUUID("99b3357d-3edf-4dfd-a6de-7a409c0be76b");  // add UUID here
    pAdvertising->setAdvertisementData(advData);

    pAdvertising->start();
    Serial.println("BLE Started");

    FastLED.addLeds<SK6812, DATA_PIN, GRB>(leds, NUM_LEDS);

    // 1. Initialize timer at 1 MHz (1 tick = 1 microsecond)
    timer = timerBegin(1000000); 

    // 2. Attach the ISR function to the timer
    timerAttachInterrupt(timer, &onTimer);

    // 3. Set alarm to trigger every 500,000 ticks (500ms), 
    // autoreload = true, reload count = 0 (unlimited)
    timerAlarm(timer, 500000, true, 0);

    // 4. Turn off pull-up.
    //gpio_set_pull_mode((gpio_num_t)1, GPIO_FLOATING);  // Or GPIO_NUM_1
    int value = gpio_pullup_dis(GPIO_NUM_1);
    Serial.printf("gpio_pullup_dis() returns %d\n", value);

    // Disable pull-up on A1 (GPIO1)
    gpio_set_pull_mode((gpio_num_t)1, GPIO_FLOATING);  // Or GPIO_NUM_1
    
    analogReadResolution(12);  // Ensure 12-bit (0-4095)
    // Optional: Set attenuation for full 0-3.3V range
    //analogSetAttenuation(ADC_11db);
    analogSetAttenuation(ADC_0db);  // Most accurate, 0-1.1V range

    return;
}

void loop()
{
  static int8_t bufIndex = 0;
  uint16_t data[NSAMPLES];
  volatile bool *pFlag;
  
  portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

  // Wait for the next buffer of data being collected by interrupt.
  pFlag=NULL;
  while(pFlag == NULL)
  {
    if((bufIndex == 0) && adcBuf0Full)
    {
      pFlag = &adcBuf0Full;
    }
    else
    if((bufIndex == 1) && adcBuf1Full)
    {
      pFlag = &adcBuf1Full;
    }
    else
    {
      // CPU stays active.  Use sleep() to use minimal power.
      delay(500);
    }

    if(pFlag)
    {
      portENTER_CRITICAL(&mux);
      memcpy(data, (uint16_t *)adcBuffer[bufIndex], sizeof(data));
      *pFlag = false;
      bufIndex ^= 1;
      portEXIT_CRITICAL(&mux);
    }
  }

  // USE THIS TO MONITOR THE BLE CONNECTED STATE WITHOUT CALLBACKS.
  // if (pServer->getConnectedCount() > 0) {
  //     // connected — sample and notify
  //     pDataChar->setValue(dataBuffer, dataLength);
  //     pDataChar->notify();
  // }

  // To transmit data (call repeatedly in loop)
  //pDataChar->setValue("2, 3, 5, 7, 9, 11");             // Set Values with a String.
  pDataChar->setValue((uint8_t *) data, sizeof(data));    // Set Values with a uint8_t array[].
  pDataChar->notify();   // <-- pushes data to connected client
  Serial.println("Data sent");

  // Blink LEDs to show activity.
  leds[0] = ++loopCount & 1 ? CRGB::Red : CRGB::Green;
  FastLED.show();

}
