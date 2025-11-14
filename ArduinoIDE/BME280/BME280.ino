#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define BME_ADDR 0x76

Adafruit_BME280 bme;

void setup() {
  Serial.begin(115200);
  if(!bme.begin(BME_ADDR)){
    Serial.println("No encuentro un sensor BME280 valido!");
    while (1);
  }
}

void loop() {
  Serial.print(bme.readTemperature());
  Serial.print(",");
  Serial.print(bme.readHumidity());
  Serial.print(",");
  Serial.println(bme.readPressure() / 100.0F);
  delay(10000);
}
