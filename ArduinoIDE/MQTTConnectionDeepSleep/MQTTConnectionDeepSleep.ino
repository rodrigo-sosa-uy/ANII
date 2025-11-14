#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <Wire.h>

#define debugMode 1

//------------  Credenciales WiFi  ------------//
#define ssid "Rodriagus"
#define password "coquito15"

#define mqtt_server "192.168.1.25"
#define mqtt_port 1883

WiFiClient espClient;
PubSubClient mqttClient(espClient);

#define inTopic "led_control"
#define outTopic "temperature"
#define buff_size 10
char msg[buff_size];

byte state = 0;

//------------  Sensor de temperatura  ------------//
float temp;

// AHT10 I2C address
#define AHT10_ADDRESS 0x38

// AHT10 registers
#define AHT10_INIT_CMD 0xE1
#define AHT10_MEASURE_CMD 0xAC
#define AHT10_RESET_CMD 0xBA

const long sleepTimeUs = 30 * 1000000; // 30 segundos

void setup() {
  if(debugMode){
    Serial.begin(115200);
    Serial.println("ESP8266 desperto!");
  }

  Wire.begin();

  pinMode(BUILTIN_LED, OUTPUT);

  initWiFi();
  initMQTT();
  initAHT10();

  working();

  if(debugMode){
    Serial.println("Entrando en Deep Sleep...");
  }
  ESP.deepSleep(sleepTimeUs);
}

void loop() {

}

void initWiFi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while(WiFi.status() != WL_CONNECTED){
    delay(500);
  }

  if(debugMode){
    Serial.println("----------------------------");
    Serial.println("Conectado a la red.");
    Serial.print("Dirección IP: "); Serial.println(WiFi.localIP());
    Serial.println("----------------------------");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  if(debugMode){
    Serial.print("Mensaje nuevo ["); Serial.print(topic); Serial.print("]: ");
    for (int i = 0; i < length; i++) {
      Serial.print((char)payload[i]);
    }
    Serial.println();
  }

  if((char)payload[5] == '1'){
    digitalWrite(BUILTIN_LED, LOW);
  } else{
    digitalWrite(BUILTIN_LED, HIGH);
  }
}

void initMQTT(){
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);

  mqttClient.subscribe(inTopic);
}

void initAHT10(){
  // Initialize AHT10 sensor
  Wire.beginTransmission(AHT10_ADDRESS);
  Wire.write(AHT10_INIT_CMD);
  Wire.endTransmission();
  delay(20); // Wait for sensor initialization
}

void pubTemperature(){
  snprintf(msg, buff_size, "TMP:%.2f", temp);

  mqttClient.publish(outTopic, msg);
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

void reconnect() { // Loop until we're reconnected
  while (! mqttClient.connected()) {
    if(debugMode){
      Serial.print("Attempting MQTT connection...");
    }
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (mqttClient.connect(clientId.c_str())) {
      if(debugMode){
        Serial.println("connected");
      }
    } else {
      if(debugMode){
        Serial.print("failed, rc="); Serial.print(mqttClient.state()); Serial.println(" try again in 5 seconds");
      }
      delay(5000); // Wait 5 seconds before retrying
    }
  }
}

void working(){
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  measureTemp();
  pubTemperature();

  if(debugMode){
    Serial.print("Publicado: [");
    Serial.print("TMP:");
    Serial.print(temp);
    Serial.println("]");
  }
}