#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

#define debugMode 1

//--------------  Credenciales MQTT  --------------//
#define mqtt_server "192.168.164.163"
//#define mqtt_server "169.254.41.250"
#define mqtt_port 1883

ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

//-------------------  Topicos  -------------------//

#define TOPIC_RADIATION "measure/radiation"

//----------  Variables de comunicacion  ----------//
#define buff_size 10
char msg[buff_size];

//-----------------  Piranometro  -----------------//
Adafruit_ADS1115 ads;

const float gain = 0.0078125;
const float cal_factor = 70.9e-3;

// Red - Radiation Signal - Pin A0
// Blue - Signal Reference - Ground
// Black - Shield - Ground

float radiation;

const long sleepTimeUs = 1 * 1000000 * 60; // 20 minutos

void setup() {
  if(debugMode){
    Serial.begin(115200);
    Serial.println("ESP8266 desperto!");
  }

  Wire.begin();

  pinMode(BUILTIN_LED, OUTPUT);

  initWiFi();
  initMQTT();
  initADS1115();

  working();

  if(debugMode){
    Serial.println("Entrando en Deep Sleep...");
  }
  ESP.deepSleep(sleepTimeUs);
}

void loop() {

}

void initWiFi(){
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  //wifiMulti.addAP("DispositivosIoT", "itrSO.iot.2012");

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
    Serial.print(" Conectado a la red: "); Serial.println(WiFi.SSID());
    Serial.print(" Dirección IP: "); Serial.println(WiFi.localIP());
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
}

void initMQTT(){
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);
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

void measureRadiation(){
  int16_t adc_value = ads.readADC_SingleEnded(0);
  float vcc_mv = adc_value * gain;

  radiation = vcc_mv / cal_factor;
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

  measureRadiation();
  pubRadiation();

  delay(1000);
}