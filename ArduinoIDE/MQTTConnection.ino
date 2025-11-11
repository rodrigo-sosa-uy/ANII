#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define debugMode 1

//------------  Credenciales WiFi  ------------//
#define ssid "Rodriagus"
#define password "coquito15"

#define mqtt_server "192.168.1.59"
#define mqtt_port 1883

WiFiClient espClient;
PubSubClient mqttClient(espClient);

//-------------------  Topicos  -------------------//

#define TOPIC_IN_VALVE "control/in_valve"
#define TOPIC_OUT_VALVE "control/out_valve"

#define TOPIC_TEMPERATURE "sens/temperature"
#define TOPIC_RADIATION "measure/radiation"
#define TOPIC_HUMIDITY "measure/humidity"

#define buff_size 10
char msg[buff_size];
unsigned long lastMsg;

byte state = 0;

//-------------  Entradas y salidas  --------------//
//#define IN_VALVE GPIOx
//#define OUT_VALVE GPIOx

//------------  Sensor de temperatura  ------------//
float temperature;
// implementar logica termocupla

//-----------------  Piranometro  -----------------//
float radiation;
// implementar logica adc externo

//--------------  Sensor de humedad  --------------//
//#define BME_ADDR 0x76

//Adafruit_BME280 bme;

int humidity;

void setup() {
  if(debugMode){
    Serial.begin(115200);
  }

  Wire.begin();

  pinMode(BUILTIN_LED, OUTPUT);

  initWiFi();
  initMQTT();
  //initBME();
}

void loop() {
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastMsg > 10000) {
    lastMsg = now;

    //measureTemp();
    pubTemperature();
    if(debugMode){
      Serial.print("Publicado: [");
      Serial.print("TMP:");
      Serial.print(temperature);
      Serial.println("]");
    }
  }
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
  Serial.print("Mensaje nuevo ["); Serial.print(topic); Serial.print("]: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  if(topic == TOPIC_IN_VALVE){
    if((char)payload[0] == '1'){
      digitalWrite(BUILTIN_LED, LOW);
    } else if((char)payload[0] == '0'){
      digitalWrite(BUILTIN_LED, HIGH);
    }
  }
}

void initMQTT(){
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);

  mqttClient.subscribe(TOPIC_IN_VALVE);
}
/*
void initBME(){
  if(!bme.begin(BME_ADDR)){
    Serial.println("No encuentro un sensor BME280 valido!");
    while (1);
  }
}
*/
void pubTemperature(){
  temperature = 10;
  snprintf(msg, buff_size, "%.2f", temperature);

  mqttClient.publish(TOPIC_TEMPERATURE, msg);
}
/*
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
    temperature = (temp_raw * (200.0 / 1048576.0)) - 50;
  }
}

void measureHumi(){
  humidity = bme.readHumidity();
}
*/
void reconnect() { // Loop until we're reconnected
  while (! mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc="); Serial.print(mqttClient.state()); Serial.println(" try again in 5 seconds");
      delay(5000); // Wait 5 seconds before retrying
    }
  }
}