/*
 * -----------------------------------------------------------------------
 * SISTEMA INTEGRAL SCADA - WEMOS D1 R2 (VERSIÓN 3.3 - LOGICA LOOP OPTIMIZADA)
 * -----------------------------------------------------------------------
 * Estado Actual:
 * - Hardware: Configuración de pines definitiva (Full IO).
 * - Comunicación: MQTT completo.
 * - Lógica Loop: 
 * > Reposo: Todo cada 15 min.
 * > Activo: Proceso cada 10 seg + Ambiente cada 15 min.
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
// 1. CONFIGURACIÓN
// =========================================================
#define DEBUG_MODE 0       

#define MQTT_SERVER "192.168.101.250"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "Wemos_SCADA_V3_Clean"

// --- TEMPORIZADORES ---
const unsigned long INTERVAL_METEO   = 15 * 60 * 1000; // 15 Minutos
const unsigned long INTERVAL_PROCESS = 10 * 1000;      // 10 Segundos (Control Activo)

// =========================================================
// 2. MAPEO DE PINES (WEMOS D1 R2 - CONFIGURACIÓN FINAL)
// =========================================================
#define PIN_RELAY_IN    1   // TX (GPIO 1)
#define PIN_RELAY_OUT   3   // RX (GPIO 3)
#define US_IN_TRIG      D1  // GPIO 5
#define US_IN_ECHO      D0  // GPIO 16
#define HX_IN_DT        D2  // GPIO 4
#define HX_IN_SCK       D8  // GPIO 15
#define PIN_I2C_SDA     D4  // GPIO 2
#define PIN_I2C_SCL     D3  // GPIO 0
#define MAX_SCK         D5  // GPIO 14
#define MAX_SO          D6  // GPIO 12
#define MAX_CS          D7  // GPIO 13

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

struct State {
  float temp_amb;
  float hum_amb;
  float pres_amb;
  float radiation;
  float temp_int;
  float lvl_in_weight;
  float lvl_in_dist;
  float chamber_amount;
  float lvl_out_dist;
  bool valve_in_state;
  bool valve_out_state;
  bool process_active;
} sysState;

unsigned long lastMeteoTime = 0;
unsigned long lastProcessTime = 0;

const float PYR_GAIN = 0.0078125;
const float PYR_CAL = 70.9e-3;
const float SCALE_CAL = 2280.0; 

const char* TP_MEAS_ENV      = "measure/environment";   
const char* TP_MEAS_RAD      = "measure/radiation";     
const char* TP_MEAS_TEMP     = "measure/temperature";   
const char* TP_MEAS_LVL_IN   = "measure/level_in";      
const char* TP_MEAS_LVL_OUT  = "measure/level_out"; 
const char* TP_MEAS_CHAMBER  = "measure/chamber_level"; 

const char* TP_CTRL_IN       = "control/in_valve";
const char* TP_CTRL_OUT      = "control/out_valve";
const char* TP_CTRL_PROCESS  = "control/process";       
const char* TP_ALARM         = "measure/alarm"; 

// =========================================================
// 4. SETUP
// =========================================================
void setup() {
  pinMode(PIN_RELAY_IN, OUTPUT);
  pinMode(PIN_RELAY_OUT, OUTPUT);
  digitalWrite(PIN_RELAY_IN, LOW);
  digitalWrite(PIN_RELAY_OUT, LOW);
  sysState.valve_in_state = false;
  sysState.valve_out_state = false;

  pinMode(US_IN_TRIG, OUTPUT);
  pinMode(US_IN_ECHO, INPUT);

  sysState.process_active = false;
  sysState.chamber_amount = 0.0;
  sysState.lvl_out_dist = 0.0;  

  initWiFi();
  initMQTT();
  initSensors();
}

// =========================================================
// 5. LOOP PRINCIPAL (OPTIMIZADO)
// =========================================================
void loop() {
  if (!mqttClient.connected()) { reconnect(); }
  mqttClient.loop();

  unsigned long now = millis();

  // --- TAREA AMBIENTAL (Lenta - 15 min) ---
  // Se ejecuta SIEMPRE, esté el proceso activo o no.
  if (now - lastMeteoTime > INTERVAL_METEO) {
    lastMeteoTime = now;
    
    measureEnvironment();
    measureRadiation();
    
    pubEnvironment();
    pubRadiation();

    // Si el proceso está INACTIVO, reportamos el estado del tanque/cámara también cada 15 min
    // para mantener un registro histórico de "reposo".
    if (!sysState.process_active) {
       measureInternalTemp();
       measureLevelIn(); 
       
       pubInternalTemp();
       pubLevelIn();
       //pubChamberLevel();
       //pubLevelOut(); 
    }
  }

  // --- TAREA PROCESO (Rápida - 10 seg) ---
  // Solo se ejecuta si el usuario activó el proceso (START)
  if (sysState.process_active) {
    if (now - lastProcessTime > INTERVAL_PROCESS) {
      lastProcessTime = now;
      
      measureInternalTemp();
      measureLevelIn(); 

      // Ejecutar lógica de control
      runProcessLogic();

      // Publicar datos de proceso con alta frecuencia
      pubInternalTemp();
      pubLevelIn();
      //pubChamberLevel(); 
      //pubLevelOut(); 
      
      // Feedback de válvulas por si hubo cierre automático
      if (!sysState.valve_in_state) mqttClient.publish(TP_CTRL_IN, "0");
    }
  }
}

// =========================================================
// 6. LÓGICA DE PROCESO
// =========================================================
void runProcessLogic() {
   // Placeholder para futura lógica de control
}

// =========================================================
// 7. INICIALIZACIÓN
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
  bme.begin(0x76);
  ads.setGain(GAIN_SIXTEEN);
  ads.begin();
  scaleIn.begin(HX_IN_DT, HX_IN_SCK);
  scaleIn.set_scale(SCALE_CAL);
  scaleIn.tare();
}

// =========================================================
// 8. MEDICIÓN
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
  digitalWrite(US_IN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(US_IN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(US_IN_TRIG, LOW);
  long dur = pulseIn(US_IN_ECHO, HIGH, 25000);
  sysState.lvl_in_dist = (dur == 0) ? -1.0 : (dur * 0.034 / 2);

  if (scaleIn.is_ready()) {
    sysState.lvl_in_weight = scaleIn.get_units(1);
  } else {
    sysState.lvl_in_weight = -99.0;
  }
}

// =========================================================
// 9. PUBLICACIÓN
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

void pubLevelOut() {
  char msg[30];
  snprintf(msg, sizeof(msg), "%.2f,%.2f", sysState.lvl_out_weight, sysState.lvl_out_dist);
  mqttClient.publish(TP_MEAS_LVL_OUT, msg);
}

void pubChamberLevel() {
  char msg[15];
  snprintf(msg, sizeof(msg), "%.3f", sysState.chamber_amount);
  mqttClient.publish(TP_MEAS_CHAMBER, msg);
}

// =========================================================
// 10. CONTROL (CALLBACK MQTT)
// =========================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  String strTopic = String(topic);
  
  bool cmdState = (msg == "1");

  if (strTopic == TP_CTRL_IN) {
    digitalWrite(PIN_RELAY_IN, cmdState ? HIGH : LOW);
    sysState.valve_in_state = cmdState;
  } 
  else if (strTopic == TP_CTRL_OUT) {
    digitalWrite(PIN_RELAY_OUT, cmdState ? HIGH : LOW);
    sysState.valve_out_state = cmdState;
  }
  else if (strTopic == TP_CTRL_PROCESS) {
    sysState.process_active = cmdState;
  }
}

void reconnect() {
  while (!mqttClient.connected()) {
    String clientId = String(MQTT_CLIENT_ID) + "-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      mqttClient.subscribe(TP_CTRL_IN);
      mqttClient.subscribe(TP_CTRL_OUT);
      mqttClient.subscribe(TP_CTRL_PROCESS);
    } else {
      delay(5000);
    }
  }
}