#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <max6675.h>
#include <Adafruit_ADS1X15.h>

#define debugMode 1

//--------------  Credenciales MQTT  --------------//
#define mqtt_server "192.168.0.xxx"
//#define mqtt_server "169.254.41.250"
#define mqtt_port 1883

ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

//-------------------  Topicos  -------------------//

#define TOPIC_IN_VALVE "control/in_valve"
#define TOPIC_OUT_VALVE "control/out_valve"

#define TOPIC_TEMPERATURE "measure/temperature"
#define TOPIC_RADIATION "measure/radiation"
#define TOPIC_HUMIDITY "measure/humidity"

//----------  Variables de comunicacion  ----------//
#define buff_size 10
char msg[buff_size];
unsigned long lastMsg;

//-------------  Entradas y salidas  --------------//
#define IN_VALVE 13    // D7
#define OUT_VALVE 15   // D8

//------------  Sensor de temperatura  ------------//
#define MAX6675_SO 2   // D4
#define MAX6675_CS 14  // D5
#define MAX6675_SCK 12 // D6

MAX6675 thermocouple(MAX6675_SCK, MAX6675_CS, MAX6675_SO);

float temperature;

//-----------------  Piranometro  -----------------//
Adafruit_ADS1115 ads;

const float gain = 0.0078125;
const float cal_factor = 70.9e-3;

// Red - Radiation Signal - Pin A0
// Blue - Signal Reference - Ground
// Black - Shield - Ground

float radiation;

//--------------  Sensor de humedad  --------------//
#define BME_ADDR 0x76

Adafruit_BME280 bme;

int humidity;

//-------------------------------------------------//

void setup() {
  if(debugMode){
    Serial.begin(115200);
  }

  Wire.begin();

  pinMode(BUILTIN_LED, OUTPUT);

  initWiFi();
  initMQTT();
  initBME();
  initMAX6675();
  initADS1115();
}

void loop() {
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastMsg > 10000) {
    lastMsg = now;

    measureTemperature();
    pubTemperature();

    measureRadiation();
    pubRadiation();

    measureHumidity();
    pubHumidity();
  }
}

void initWiFi(){
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  wifiMulti.addAP("Rodriagus", "coquito15");
  wifiMulti.addAP("DispositivosIoT", "itrSO.iot.2012");

  while(wifiMulti.run() != WL_CONNECTED){
    digitalWrite(BUILTIN_LED, LOW);
    delay(250);
    digitalWrite(BUILTIN_LED, HIGH);
    delay(250);

    if(debugMode){
      Serial.print(". ");
    }
  }

  if(debugMode){
    Serial.println("----------------------------");
    Serial.println(" Conectado a la red.");
    Serial.print(" Dirección IP: "); Serial.println(WiFi.localIP());
    Serial.println("----------------------------");
  }
}

void initBME(){
  if(!bme.begin(BME_ADDR)){
    if(debugMode){
      Serial.println("############################################");
      Serial.println("### No encuentro un sensor BME280 valido ###");
      Serial.println("############################################");
    }
    for(int i = 0; i < 10; i++){
      digitalWrite(BUILTIN_LED, LOW);
      delay(50);
      digitalWrite(BUILTIN_LED, HIGH);
      delay(50);
    }
  } else{
    if(debugMode){
      Serial.println("Sensor BME Inicializado.");
    }
  }
}

void initMAX6675(){
  pinMode(MAX6675_CS, OUTPUT);
  pinMode(MAX6675_SO, INPUT);
  pinMode(MAX6675_SCK, OUTPUT);

  if(debugMode){
    Serial.println("MAX6675 Inicializado.");
  }
}

void initADS1115(){
  ads.setGain(GAIN_SIXTEEN);
  if (!ads.begin()) {
    if(debugMode){
      Serial.println("############################################");
      Serial.println("#### No encuentro un piranometro valido ####");
      Serial.println("############################################");
    }
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

  // ---------- Controla el proceso ----------
  if(topic == TOPIC_IN_VALVE){
    if((char)payload[0] == '1'){
      digitalWrite(IN_VALVE, HIGH);
    } else if((char)payload[0] == '0'){
      digitalWrite(IN_VALVE, LOW);
    }
  } else if(topic == TOPIC_OUT_VALVE){
    if((char)payload[0] == '1'){
      digitalWrite(OUT_VALVE, HIGH);
    } else if((char)payload[0] == '0'){
      digitalWrite(OUT_VALVE, LOW);
    }
  }
}

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

void initMQTT(){
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);

  mqttClient.subscribe(TOPIC_IN_VALVE);
  mqttClient.subscribe(TOPIC_OUT_VALVE);

  if(debugMode){
    Serial.println("MQTT Inicializado.");
  }
}

void measureTemperature(){
  temperature = thermocouple.readCelsius();
}

void measureRadiation(){
  int16_t adc_value = ads.readADC_SingleEnded(0);
  int16_t vcc_mv = adc_value * gain;

  radiation = vcc_mv / cal_factor;
}

void measureHumidity(){
  humidity = bme.readHumidity();
}

void pubTemperature(){
  snprintf(msg, buff_size, "%.2f", temperature);

  mqttClient.publish(TOPIC_TEMPERATURE, msg);

  if(debugMode){
    Serial.print("Publicado: [");
    Serial.print(TOPIC_TEMPERATURE);
    Serial.print("]: ");
    Serial.println(temperature);
  }
}

void pubRadiation(){
  snprintf(msg, buff_size, "%.2f", radiation);

  mqttClient.publish(TOPIC_RADIATION, msg);

  if(debugMode){
    Serial.print("Publicado: [");
    Serial.print(TOPIC_RADIATION);
    Serial.print("]: ");
    Serial.println(radiation);
  }
}

void pubHumidity(){
  snprintf(msg, buff_size, "%i", humidity);

  mqttClient.publish(TOPIC_HUMIDITY, msg);

  if(debugMode){
    Serial.print("Publicado: [");
    Serial.print(TOPIC_HUMIDITY);
    Serial.print("]: ");
    Serial.println(humidity);
  }
}