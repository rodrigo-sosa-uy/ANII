#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

#define debugMode 0

//--------------  Credenciales MQTT  --------------//
#define mqtt_server "192.168.101.250"
//#define mqtt_server "169.254.41.250"
#define mqtt_port 1883

ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

//-------------------  Topicos  -------------------//

#define TOPIC_RADIATION "measure/radiation"
#define TOPIC_CTRL "control/sampletime"

//----------  Variables de comunicacion  ----------//
#define buff_size 10
char msg[buff_size];
unsigned long lastMsg;
unsigned long waitTime = 15 * 60 * 1000;

//-----------------  Piranometro  -----------------//
Adafruit_ADS1115 ads;

const float gain = 0.0078125;
const float cal_factor = 70.9e-3;

// Red - Radiation Signal - Pin A0
// Blue - Signal Reference - Ground
// Black - Shield - Ground

float radiation;

bool fg = true;

void setup() {
  if(debugMode){
    Serial.begin(115200);
  }

  Wire.begin();

  pinMode(BUILTIN_LED, OUTPUT);

  initWiFi();
  initMQTT();
  initADS1115();
}

void loop() {
  working();
}

void initWiFi(){
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  //wifiMulti.addAP("DispositivosIoT", "itrSO.iot.2012");
  wifiMulti.addAP("UTEC-Invitados", "");

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

  if(debugMode){
    Serial.println("MQTT Inicializado.");
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

void measureRadiation(){
  long adc_accumulated = 0; // Variable para sumar las lecturas
  int samples = 10;         // Número de muestras a promediar

  for (int i = 0; i < samples; i++) {
    adc_accumulated += ads.readADC_SingleEnded(0);
    delay(20); // Pequeña pausa de 20ms entre lecturas para estabilizar ruido
  }

  // Calculamos el promedio de los valores crudos del ADC
  float avg_adc_value = (float)adc_accumulated / samples;
  
  // Convertimos el promedio a voltaje y luego a radiación
  float vcc_mv = avg_adc_value * gain;
  radiation = vcc_mv / cal_factor;
  delay(10);
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

  if(fg){
    measureRadiation();
    pubRadiation();
    fg = false;
  }

  unsigned long now = millis();
  if (now - lastMsg > waitTime) {
    lastMsg = now;

    measureRadiation();
    pubRadiation();
  }
}