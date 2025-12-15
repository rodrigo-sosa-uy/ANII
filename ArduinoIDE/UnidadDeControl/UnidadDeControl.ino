/*
 * -----------------------------------------------------------------------
 * SISTEMA INTEGRAL SCADA - WEMOS D1 R2 (VERSIÓN 2.0)
 * -----------------------------------------------------------------------
 * Cambios V2:
 * - Tópicos de nivel separados (level_in / level_out)
 * - Tópico de control de proceso general (control/process)
 * - Estructura preparada para expansión futura
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
#define DEBUG_MODE 0       // 0 OBLIGATORIO si usas pines TX/RX para sensores

// --- RED Y MQTT ---
#define MQTT_SERVER "192.168.1.250"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "Wemos_SO"

// --- TEMPORIZADORES ---
const unsigned long INTERVAL_METEO   = 15 * 60 * 1000; // 15 Minutos
const unsigned long INTERVAL_PROCESS = 15 * 1000;       // 15 Segundos

// =========================================================
// 2. MAPEO DE PINES (WEMOS D1 R2)
// =========================================================

// I2C (BME + ADS)
#define PIN_I2C_SDA     D4
#define PIN_I2C_SCL     D3

// TERMOCUPLA (SPI SW)
#define MAX_SCK         D5
#define MAX_SO          D6
#define MAX_CS          D7

// ACTUADORES
#define PIN_RELAY_IN    D9  
#define PIN_RELAY_OUT   D10 

// NIVEL ENTRADA (HX711)
#define HX_IN_DT        D2  
#define HX_IN_SCK       D8  

// NIVEL ENTRADA (ULTRASONIDO) -> Pines Serial
#define US_IN_TRIG      D1  // TX
#define US_IN_ECHO      D0  // RX

// =========================================================
// 3. OBJETOS Y VARIABLES
// =========================================================
ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

Adafruit_BME280 bme;
Adafruit_ADS1115 ads;
MAX6675 thermocouple(MAX_SCK, MAX_CS, MAX_SO);
HX711 scaleIn;

// Estado del Sistema
struct State {
  float temp_amb;
  float hum_amb;
  float pres_amb;
  float radiation;
  float temp_int;
  
  // Nivel Entrada
  float lvl_in_weight;
  float lvl_in_dist;
  
  // Nivel Salida (Futuro)
  float lvl_out_weight;
  float lvl_out_dist;

  // Estado del Proceso
  bool process_active; // True = ON, False = OFF
} sysState;

unsigned long lastMeteoTime = 0;
unsigned long lastProcessTime = 0;

// Constantes
const float PYR_GAIN = 0.0078125;
const float PYR_CAL = 70.9e-3;
const float SCALE_CAL = 2280.0;

// --- DEFINICIÓN DE TÓPICOS (V2.0) ---
const char* TP_MEAS_ENV      = "measure/environment";   // T,H,P
const char* TP_MEAS_RAD      = "measure/radiation";     // Rad
const char* TP_MEAS_TEMP     = "measure/temperature";   // T_Int
const char* TP_MEAS_LVL_IN   = "measure/level_in";      // Peso,Dist (Entrada)
const char* TP_MEAS_LVL_OUT  = "measure/level_out";     // Peso,Dist (Salida)

const char* TP_CTRL_IN       = "control/in_valve";
const char* TP_CTRL_OUT      = "control/out_valve";
const char* TP_CTRL_PROCESS  = "control/process";       // General Start/Stop

// =========================================================
// 4. SETUP
// =========================================================
void setup() {
  if (DEBUG_MODE) {
    Serial.begin(115200);
    Serial.println("INIT");
  }

  // Pines Salida
  pinMode(PIN_RELAY_IN, OUTPUT);
  pinMode(PIN_RELAY_OUT, OUTPUT);
  digitalWrite(PIN_RELAY_IN, LOW);
  digitalWrite(PIN_RELAY_OUT, LOW);

  pinMode(US_IN_TRIG, OUTPUT);
  pinMode(US_IN_ECHO, INPUT);

  // Estado inicial
  sysState.process_active = false;
  sysState.lvl_out_weight = 0.0; // Placeholder futuro
  sysState.lvl_out_dist = 0.0;   // Placeholder futuro

  initWiFi();
  initMQTT();
  initSensors();
}

// =========================================================
// 5. LOOP
// =========================================================
void loop() {
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  unsigned long now = millis();

  // --- TAREA AMBIENTAL (Lenta) ---
  if (now - lastMeteoTime > INTERVAL_METEO) {
    lastMeteoTime = now;
    measureEnvironment();
    measureRadiation();

    pubEnvironment();
    pubRadiation();

    if (!sysState.process_active){
      measureInternalTemp();
      measureLevelIn();
      // measureLevelOut(); // Futuro

      pubInternalTemp();
      pubLevelIn();
      //pubLevelOut(); // Futuro
    }
  }

  // --- TAREA PROCESO (Rápida) ---
  if (sysState.process_active) {
    if (now - lastProcessTime > INTERVAL_PROCESS) {
      lastProcessTime = now;
      measureInternalTemp();
      measureLevelIn();
      // measureLevelOut(); // Futuro

      pubInternalTemp();
      pubLevelIn();
      //pubLevelOut(); // Futuro
    }

    // Aca va la lógica de control, apertura de valvula controlada
  }
}

// =========================================================
// 6. INIT SUBSISTEMAS
// =========================================================
void initWiFi() {
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  wifiMulti.addAP("Rodriagus", "coquito15");
  wifiMulti.addAP("UTEC-Invitados", "");
  while (wifiMulti.run() != WL_CONNECTED) { delay(500); }
}

void initMQTT() {
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void initSensors() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (!bme.begin(0x76)) { /* Err */ }
  
  ads.setGain(GAIN_SIXTEEN);
  if (!ads.begin()) { /* Err */ }

  scaleIn.begin(HX_IN_DT, HX_IN_SCK);
  scaleIn.set_scale(SCALE_CAL);
  scaleIn.tare();
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

void measureLevelIn() {
  // Ultrasonido In
  digitalWrite(US_IN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(US_IN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(US_IN_TRIG, LOW);
  long dur = pulseIn(US_IN_ECHO, HIGH, 25000);
  sysState.lvl_in_dist = (dur == 0) ? -1.0 : (dur * 0.034 / 2);

  // Peso In
  if (scaleIn.is_ready()) {
    sysState.lvl_in_weight = scaleIn.get_units(1);
  } else {
    sysState.lvl_in_weight = -99.0;
  }
}

// =========================================================
// 8. PUBLICACIÓN
// =========================================================
void pubEnvironment() {
  char msg[50];
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
  snprintf(msg, sizeof(msg), "%.2f", sysState.temp_int);
  mqttClient.publish(TP_MEAS_TEMP, msg);
}

void pubLevelIn() {
  char msg[30];
  snprintf(msg, sizeof(msg), "%.2f,%.2f", sysState.lvl_in_weight, sysState.lvl_in_dist);
  mqttClient.publish(TP_MEAS_LVL_IN, msg);
}
/*
void pubLevelOut() {
  char msg[30];
  // Placeholder para el futuro
  snprintf(msg, sizeof(msg), "%.2f,%.2f", sysState.lvl_out_weight, sysState.lvl_out_dist);
  mqttClient.publish(TP_MEAS_LVL_OUT, msg);
}
*/
// =========================================================
// 9. CONTROL (CALLBACK)
// =========================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  String strTopic = String(topic);

  // 1. Control Válvula Entrada
  if (strTopic == TP_CTRL_IN) {
    digitalWrite(PIN_RELAY_IN, (msg == "1" ? HIGH : LOW));
  } 
  // 2. Control Válvula Salida
  else if (strTopic == TP_CTRL_OUT) {
    digitalWrite(PIN_RELAY_OUT, (msg == "1" ? HIGH : LOW));
  }
  // 3. Control Proceso General (Start/Stop)
  else if (strTopic == TP_CTRL_PROCESS) {
    sysState.process_active = (msg == "1");
    // Feedback inmediato o acciones al detener
    if (!sysState.process_active) {
       digitalWrite(PIN_RELAY_IN, LOW);
    }
  }
}

void reconnect() {
  while (!mqttClient.connected()) {
    String clientId = String(MQTT_CLIENT_ID) + "-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      // Suscribirse a TODOS los canales de control
      mqttClient.subscribe(TP_CTRL_IN);
      mqttClient.subscribe(TP_CTRL_OUT);
      mqttClient.subscribe(TP_CTRL_PROCESS);
    } else {
      delay(5000);
    }
  }
}