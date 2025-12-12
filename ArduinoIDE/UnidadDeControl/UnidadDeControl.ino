/*
 * -----------------------------------------------------------------------
 * SISTEMA INTEGRAL SCADA - WEMOS D1 R2 (VERSIÓN DOBLE NIVEL)
 * -----------------------------------------------------------------------
 * Mapeo de Hardware:
 * - I2C (D3/D4): BME280 (Ambiente) + ADS1115 (Radiación)
 * - SPI (D5/D6/D7): 1x MAX6675 (Temp Interna)
 * - GPIO:
 * - D9, D10: Relés (Válvulas)
 * - D2, D8: HX711 (Peso)
 * - D1, D0: HC-SR04 (Distancia) -> ¡Usa pines Serial!
 * -----------------------------------------------------------------------
 */

#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <max6675.h>
#include <Adafruit_ADS1X15.h>
#include <HX711.h> 

// =========================================================
// 1. CONFIGURACIÓN DEL SISTEMA
// =========================================================
// Poner en 0 si usas los pines D0/D1 para el sensor, ya que bloquean el Serial
#define DEBUG_MODE 0       

// --- RED Y MQTT ---
#define MQTT_SERVER "192.168.101.250"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "Wemos_Control_SO"

// --- TEMPORIZADORES (Milisegundos) ---
const unsigned long INTERVAL_METEO   = 15 * 60 * 1000; // 15 Minutos
const unsigned long INTERVAL_PROCESS = 2 * 1000;       // 2 Segundos

// =========================================================
// 2. MAPEO DE PINES (WEMOS D1 R2)
// =========================================================

// --- I2C BUS ---
#define PIN_I2C_SDA     D4
#define PIN_I2C_SCL     D3

// --- TERMOCUPLA (SPI) ---
#define MAX_SCK         D5
#define MAX_SO          D6
#define MAX_CS          D7  // Solo una termocupla

// --- ACTUADORES (RELÉS) ---
// Usamos D9 y D10
#define PIN_RELAY_IN    D9  
#define PIN_RELAY_OUT   D10 

// --- NIVEL: PESO (HX711) ---
// Usamos D2 y D8
#define HX_DT           D2  
#define HX_SCK          D8  

// --- NIVEL: DISTANCIA (ULTRASONIDO) ---
// Usamos los pines del puerto Serial (TX/RX)
#define US_TRIG         D1  // TX
#define US_ECHO         D0  // RX

// =========================================================
// 3. OBJETOS Y VARIABLES
// =========================================================
ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

Adafruit_BME280 bme;
Adafruit_ADS1115 ads;
MAX6675 thermocouple(MAX_SCK, MAX_CS, MAX_SO);
HX711 scale;

struct State {
  float temp_amb;
  float hum_amb;
  float pres_amb;
  float radiation;
  float temp_int;     // Solo una temp interna
  float level_weight; // Peso en Kg
  float level_dist;   // Distancia en cm
} sysState;

unsigned long lastMeteoTime = 0;
unsigned long lastProcessTime = 0;

// Calibración
const float PYR_GAIN = 0.0078125;
const float PYR_CAL = 70.9e-3;
const float SCALE_CAL = 2280.0; // AJUSTAR CON PESO CONOCIDO

// Tópicos Definitivos
const char* TP_MEAS_TEMP = "measure/temperature";   // Dato único: Temp Interna
const char* TP_MEAS_RAD  = "measure/radiation";     // Dato único: Radiación
const char* TP_MEAS_ENV  = "measure/environment";   // CSV: TempAmb, Hum, Presion
const char* TP_MEAS_LVL  = "measure/level";         // CSV: Peso, Distancia
const char* TP_CTRL_IN   = "control/in_valve";
const char* TP_CTRL_OUT  = "control/out_valve";

// =========================================================
// 4. SETUP
// =========================================================
void setup() {
  if (DEBUG_MODE) {
    Serial.begin(115200);
    Serial.println("\n>>> INICIO <<<");
  }

  // Configurar Pines
  pinMode(PIN_RELAY_IN, OUTPUT);
  pinMode(PIN_RELAY_OUT, OUTPUT);
  digitalWrite(PIN_RELAY_IN, LOW);
  digitalWrite(PIN_RELAY_OUT, LOW);

  pinMode(US_TRIG, OUTPUT);
  pinMode(US_ECHO, INPUT);

  // Iniciar Módulos
  initWiFi();
  initMQTT();
  initSensors();
}

// =========================================================
// 5. LOOP PRINCIPAL
// =========================================================
void loop() {
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  unsigned long now = millis();

  // Tarea Lenta (Ambiente)
  if (now - lastMeteoTime > INTERVAL_METEO) {
    lastMeteoTime = now;
    measureEnvironment();
    measureRadiation();
    
    pubEnvironment();
    pubRadiation();
  }

  // Tarea Rápida (Proceso)
  if (now - lastProcessTime > INTERVAL_PROCESS) {
    lastProcessTime = now;
    measureInternalTemp();
    measureLevel();

    pubInternalTemp();
    pubLevel();
  }
}

// =========================================================
// 6. INICIALIZACIÓN
// =========================================================
void initWiFi() {
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  wifiMulti.addAP("Rodriagus", "coquito15");
  wifiMulti.addAP("UTEC-Invitados", "");

  while (wifiMulti.run() != WL_CONNECTED) {
    delay(500);
  }
}

void initMQTT() {
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void initSensors() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

  if (!bme.begin(0x76)) { /* Error BME */ }
  
  ads.setGain(GAIN_SIXTEEN);
  if (!ads.begin()) { /* Error ADS */ }

  scale.begin(HX_DT, HX_SCK);
  scale.set_scale(SCALE_CAL);
  scale.tare(); // Asume tanque vacío al iniciar
}

// =========================================================
// 7. MEDICIÓN
// =========================================================
void measureEnvironment() {
  sysState.temp_amb = bme.readTemperature();
  sysState.hum_amb = bme.readHumidity();
  sysState.pres_amb = bme.readPressure() / 100.0F;
}

void measureRadiation() {
  long adc_acc = 0;
  for (int i = 0; i < 20; i++) {
    adc_acc += ads.readADC_SingleEnded(0);
    delay(10);
  }
  float avg = (float)adc_acc / 20.0;
  float voltage = avg * PYR_GAIN;
  sysState.radiation = (voltage < 0) ? 0 : (voltage / PYR_CAL);
}

void measureInternalTemp() {
  sysState.temp_int = thermocouple.readCelsius();
  if (isnan(sysState.temp_int)) sysState.temp_int = -1.0;
}

void measureLevel() {
  // 1. Ultrasonido
  digitalWrite(US_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(US_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(US_TRIG, LOW);
  
  long duration = pulseIn(US_ECHO, HIGH, 25000); // 25ms timeout
  if (duration == 0) {
    sysState.level_dist = -1.0;
  } else {
    sysState.level_dist = duration * 0.034 / 2;
  }

  // 2. Celdas de Carga
  if (scale.is_ready()) {
    sysState.level_weight = scale.get_units(1);
  } else {
    sysState.level_weight = -99.0;
  }
}

// =========================================================
// 8. PUBLICACIÓN
// =========================================================
void pubEnvironment() {
  char msg[50];
  // Formato CSV Limpio: Temp, Hum, Presion
  snprintf(msg, sizeof(msg), "%.2f,%.2f,%.2f", sysState.temp_amb, sysState.hum_amb, sysState.pres_amb);
  mqttClient.publish(TP_MEAS_ENV, msg);
}

void pubRadiation() {
  char msg[15];
  snprintf(msg, sizeof(msg), "%.2f", sysState.radiation);
  mqttClient.publish(TP_MEAS_RAD, msg);
}

void pubInternalTemp() {
  char msg[10];
  // Valor único limpio (Float)
  snprintf(msg, sizeof(msg), "%.2f", sysState.temp_int);
  mqttClient.publish(TP_MEAS_TEMP, msg);
}

void pubLevel() {
  char msg[30];
  // CSV: Peso(kg), Distancia(cm)
  snprintf(msg, sizeof(msg), "%.2f,%.2f", sysState.level_weight, sysState.level_dist);
  mqttClient.publish(TP_MEAS_LVL, msg);
}

// =========================================================
// 9. CONTROL
// =========================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  if (String(topic) == TP_CTRL_IN) {
    digitalWrite(PIN_RELAY_IN, (msg == "1" ? HIGH : LOW));
  } else if (String(topic) == TP_CTRL_OUT) {
    digitalWrite(PIN_RELAY_OUT, (msg == "1" ? HIGH : LOW));
  }
}

void reconnect() {
  while (!mqttClient.connected()) {
    String clientId = "WemosR2-";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      mqttClient.subscribe(TP_CTRL_IN);
      mqttClient.subscribe(TP_CTRL_OUT);
    } else {
      delay(5000);
    }
  }
}