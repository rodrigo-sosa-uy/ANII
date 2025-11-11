#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

const float gain = 0.0078125;
const float cal_factor = 70.9e-3;

float radiacion;
int vcc_mv;

// Red - Radiation Signal - Pin A0
// Blue - Signal Reference - Ground
// Black - Shield - Ground

// Salida de señal - 0 a 120 mV

void setup() {
  Serial.begin(115200);

  ads.setGain(GAIN_SIXTEEN);    // 16x gain  +/- 0.256V  1 bit = 0.125mV  0.0078125mV

  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS.");
    while (1);
  }
}

void loop() {
  int16_t adc_value = ads.readADC_SingleEnded(0);

  Serial.print("adc_value: ");
  Serial.println(adc_value); // Print

  vcc_mv = adc_value * gain;

  Serial.print("vcc_mv: ");
  Serial.println(vcc_mv); // Print

  radiacion = vcc_mv / cal_factor;
  
  Serial.print("Radiacion: ");
  Serial.print(radiacion); // Print
  Serial.println(" W.m^-2");
  
  delay(3000); // Wait for 5 seconds
}
