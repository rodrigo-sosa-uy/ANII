#include <Wire.h>

#define debugMode 1

const long sleepTimeUs = 15 * 1000000; // 15 segundos

//------------  Sensor de temperatura  ------------//
float temp;

// AHT10 I2C address
#define AHT10_ADDRESS 0x38

// AHT10 registers
#define AHT10_INIT_CMD 0xE1
#define AHT10_MEASURE_CMD 0xAC
#define AHT10_RESET_CMD 0xBA

void setup() {
  if(debugMode){
    Serial.begin(115200);
    Serial.println("[Awaken]");
  }

  Wire.begin();
  initAHT10();

  working();

  if(debugMode){
    Serial.println("[Deep Sleep Mode]");
  }
  ESP.deepSleep(sleepTimeUs);
}

void loop() {
  // put your main code here, to run repeatedly:

}

void initAHT10(){
  // Initialize AHT10 sensor
  Wire.beginTransmission(AHT10_ADDRESS);
  Wire.write(AHT10_INIT_CMD);
  Wire.endTransmission();
  delay(20); // Wait for sensor initialization
}

void measureTemp(){
  // Trigger a measurement
  Wire.beginTransmission(AHT10_ADDRESS);
  Wire.write(AHT10_MEASURE_CMD);
  Wire.write(0x33);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(100); // Measurement time
  
  // Read the data (6 bytes)
  Wire.requestFrom(AHT10_ADDRESS, 6);
  if (Wire.available() == 6) {
    uint8_t data[6];
    for (int i = 0; i < 6; i++) {
      data[i] = Wire.read();
    }
    
    // Convert the data to actual humidity and temperature
    //unsigned long humidity_raw = ((unsigned long)data[1] << 12) | ((unsigned long)data[2] << 4) | (data[3] >> 4);
    unsigned long temp_raw = (((unsigned long)data[3] & 0x0F) << 16) | ((unsigned long)data[4] << 8) | data[5];
    
    //float humidity = humidity_raw * (100.0 / 1048576.0);
    temp = (temp_raw * (200.0 / 1048576.0)) - 50;
  }
}

void working(){
  measureTemp();
  if(debugMode){
    Serial.print("Medido: [");
    Serial.print("TMP: "); Serial.print(temp);
    Serial.println("]");
  }
}