/*
 * -----------------------------------------------------------------------
 * SISTEMA INTEGRAL SCADA - WEMOS D1 R2 (VERSIÓN ROB TILLAART FIX)
 * -----------------------------------------------------------------------
 * Correcciones:
 * 1. Implementación correcta librería Rob Tillaart MAX6675.
 * 2. Constructor actualizado a (CS, SO, SCK).
 * 3. Inicialización begin() agregada.
 * 4. Lectura por pasos status = read() -> getTemperature().
 * -----------------------------------------------------------------------
 */

#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MAX6675.h>  // Librería de Rob Tillaart
#include <Adafruit_ADS1X15.h>
#include <HX711.h> 

// =========================================================
// 1. CONFIGURACIÓN
// =========================================================
#define DEBUG_MODE 0     

// ⚠️ ATENCIÓN: VERIFICA QUE ESTA IP SEA LA DE TU BROKER
#define MQTT_SERVER "192.168.1.250" 
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "Wemos_SCADA_Debug"

// --- TEMPORIZADORES ---
const unsigned long INTERVAL_METEO   = 15 * 60 * 1000; // 15 Minutos
const unsigned long INTERVAL_PROCESS = 10000;          // 10 Segundos
bool firstRun = true; // Bandera para primer envío

// =========================================================
// 2. MAPEO DE PINES (TU CONFIGURACIÓN)
// =========================================================
#define PIN_RELAY_IN    1   // TX
#define PIN_RELAY_OUT   3   // RX

#define PIN_I2C_SCL     5   // D1
#define PIN_I2C_SDA     4   // D2

#define MAX_SCK         14  // D5
#define MAX_SO          12  // D6
#define MAX_CS          13  // D7

#define US_IN_TRIG      15  // D8
#define US_IN_ECHO      16  // D0

#define HX_IN_DT        2   // D4
#define HX_IN_SCK       0   // D3

// =========================================================
// 3. OBJETOS Y VARIABLES
// =========================================================
ESP8266WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

Adafruit_BME280 bme;
Adafruit_ADS1115 ads;

MAX6675 thermocouple(MAX_CS, MAX_SO, MAX_SCK);

HX711 scaleIn;

struct State {
  float temp_amb;
  float hum_amb;
  float pres_amb;
  float radiation;
  float temp_int;
  float lvl_in_weight;
  float lvl_in_dist;
  float lvl_out_weight;
  float lvl_out_dist;   
  float chamber_amount; 
  bool valve_in_state;
  bool valve_out_state;
  bool process_active;
} sysState;

unsigned long lastMeteoTime = 0;
unsigned long lastProcessTime = 0;

// Constantes
const float PYR_GAIN = 0.0078125;
const float PYR_CAL = 70.9e-3;
const float SCALE_CAL = 2280.0; 

// Tópicos
const char* TP_MEAS_ENV      = "measure/environment";   
const char* TP_MEAS_RAD      = "measure/radiation";     
const char* TP_MEAS_TEMP     = "measure/temperature";   
const char* TP_MEAS_LVL_IN   = "measure/level_in";      
const char* TP_MEAS_LVL_OUT  = "measure/level_out"; 
const char* TP_MEAS_CHAMBER  = "measure/chamber_level"; 

const char* TP_CTRL_IN       = "control/in_valve";
const char* TP_CTRL_OUT      = "control/out_valve";
const char* TP_CTRL_PROCESS  = "control/process";

// =========================================================
// 4. SETUP
// =========================================================
void setup() {
  if (DEBUG_MODE) {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n\n>>> INICIANDO SISTEMA <<<");
  } else {
    pinMode(PIN_RELAY_IN, OUTPUT);
    pinMode(PIN_RELAY_OUT, OUTPUT);
    digitalWrite(PIN_RELAY_IN, LOW);
    digitalWrite(PIN_RELAY_OUT, LOW);
  }
  
  sysState.valve_in_state = false;
  sysState.valve_out_state = false;

  pinMode(US_IN_TRIG, OUTPUT);
  pinMode(US_IN_ECHO, INPUT);
  digitalWrite(US_IN_TRIG, LOW);

  sysState.process_active = false;
  sysState.chamber_amount = -1.0;
  sysState.lvl_out_weight = -1.0;
  sysState.lvl_out_dist = -1.0;  

  initWiFi();
  initMQTT();
  initSensors();
  
  if (DEBUG_MODE) Serial.println(">>> SETUP COMPLETADO <<<");
}

// =========================================================
// 5. LOOP PRINCIPAL
// =========================================================
void loop() {
  if (!mqttClient.connected()) { 
    if (DEBUG_MODE) Serial.println("MQTT Desconectado. Entrando a reconnect()...");
    reconnect(); 
  }
  mqttClient.loop();

  unsigned long now = millis();

  // --- TAREA AMBIENTAL ---
  if ((now - lastMeteoTime > INTERVAL_METEO) || firstRun) {
    lastMeteoTime = now;
    
    if (DEBUG_MODE) Serial.println(">>> EJECUTANDO TAREA AMBIENTAL <<<");
    
    measureEnvironment();
    measureRadiation();
    
    pubEnvironment();
    pubRadiation();
    
    if (!sysState.process_active) {
       measureInternalTemp();
       measureLevelIn();
       pubInternalTemp();
       pubLevelIn();
    }
    
    if (firstRun) {
        if (DEBUG_MODE) Serial.println(">>> Primer envío completado <<<");
        firstRun = false;
    }
  }

  // --- TAREA PROCESO ---
  if (sysState.process_active) {
    if (now - lastProcessTime > INTERVAL_PROCESS) {
      lastProcessTime = now;
      if (DEBUG_MODE) Serial.println(">>> Ejecutando Tarea Proceso <<<");
      
      measureInternalTemp();
      measureLevelIn(); 
      runProcessLogic();

      pubInternalTemp();
      pubLevelIn();
    }
  }
}

// =========================================================
// 6. LÓGICA DE PROCESO
// =========================================================
void runProcessLogic() {
   if (sysState.process_active) {
      // Placeholder
   }
}

// =========================================================
// 7. INICIALIZACIÓN
// =========================================================
void initWiFi() {
  wifiMulti.addAP("Wifi para pobres", "1234567890");
  wifiMulti.addAP("Rodriagus", "coquito15");
  wifiMulti.addAP("UTEC-Invitados", "");
  
  if (DEBUG_MODE) Serial.print("Conectando WiFi...");
  
  int attempts = 0;
  while (wifiMulti.run() != WL_CONNECTED) {
    delay(500);
    if (DEBUG_MODE) Serial.print(".");
    attempts++;
    if(attempts > 40) { 
        if (DEBUG_MODE) Serial.println("\nNo se pudo conectar a WiFi. Reiniciando...");
        ESP.restart();
    }
  }
  
  if (DEBUG_MODE) {
    Serial.println("\nWiFi Conectado.");
    Serial.print("IP: "); Serial.println(WiFi.localIP());
  }
}

void initMQTT() {
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void initSensors() {
  if (DEBUG_MODE) Serial.println("Iniciando I2C...");
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL); 
  
  if (!bme.begin(0x76)) {
    if (DEBUG_MODE) Serial.println("⚠️ ERROR: BME280 no encontrado");
  }
  
  ads.setGain(GAIN_SIXTEEN);
  if (!ads.begin()) {
    if (DEBUG_MODE) Serial.println("⚠️ ERROR: ADS1115 no encontrado");
  }

  if (DEBUG_MODE) Serial.println("Iniciando MAX6675...");
  thermocouple.begin(); 

  // --- HX711 COMENTADO ---
  /*
  if (DEBUG_MODE) Serial.println("Iniciando HX711...");
  scaleIn.begin(HX_IN_DT, HX_IN_SCK);
  scaleIn.set_scale(SCALE_CAL);
  scaleIn.tare();
  */
}

// =========================================================
// 8. MEDICIÓN
// =========================================================
void measureEnvironment() {
  sysState.temp_amb = bme.readTemperature();
  sysState.hum_amb = bme.readHumidity();
  sysState.pres_amb = bme.readPressure() / 100.0F;
  if (DEBUG_MODE) Serial.printf("Env: T=%.2f H=%.2f P=%.2f\n", sysState.temp_amb, sysState.hum_amb, sysState.pres_amb);
}

void measureRadiation() {
  // LÓGICA COMENTADA
  /*
  long adc_acc = 0;
  for (int i = 0; i < 20; i++) {
    adc_acc += ads.readADC_SingleEnded(0);
    delay(10);
  }
  float avg = (float)adc_acc / 20.0;
  float voltage = avg * PYR_GAIN;
  sysState.radiation = (voltage < 0) ? 0 : (voltage / PYR_CAL);
  */
  sysState.radiation = 0.0; // Placeholder
}

void measureInternalTemp() {
  // CORRECCIÓN: Librería Rob Tillaart
  // 1. Leer estado
  int status = thermocouple.read(); 
  
  // 2. Obtener temperatura según estado
  if (status == STATUS_OK) {
    sysState.temp_int = thermocouple.getTemperature();
  } else {
    sysState.temp_int = -1.0; // Error de lectura
    if (DEBUG_MODE) {
      Serial.print("MAX6675 Error: ");
      Serial.println(status); // 4=Open, 128=No comms
    }
  }
  
  if (DEBUG_MODE) Serial.printf("Temp Int: %.2f\n", sysState.temp_int);
}

void measureLevelIn() {
  // ULTRASONIDO - Secuencia de disparo estándar
  digitalWrite(US_IN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(US_IN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(US_IN_TRIG, LOW);
  
  // Lectura estándar (sin timeout explícito, usa default)
  long duration = pulseIn(US_IN_ECHO, HIGH);
  
  // Cálculo
  sysState.lvl_in_dist = duration * 0.034 / 2;

  // Peso (COMENTADO)
  /*
  if (scaleIn.is_ready()) {
    sysState.lvl_in_weight = scaleIn.get_units(1);
  } else {
    sysState.lvl_in_weight = -99.0;
  }
  */
  sysState.lvl_in_weight = -1.0; 
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

// =========================================================
// 10. CONTROL
// =========================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  String strTopic = String(topic);
  
  if (DEBUG_MODE) Serial.printf("MQTT RX: %s -> %s\n", topic, msg.c_str());

  if (strTopic == TP_CTRL_PROCESS) {
    sysState.process_active = (msg == "1");
    if (DEBUG_MODE) Serial.printf("Proceso: %s\n", sysState.process_active ? "ON" : "OFF");
  }
  
  if (!DEBUG_MODE) {
      if (strTopic == TP_CTRL_IN) {
        digitalWrite(PIN_RELAY_IN, (msg == "1" ? HIGH : LOW));
      } else if (strTopic == TP_CTRL_OUT) {
        digitalWrite(PIN_RELAY_OUT, (msg == "1" ? HIGH : LOW));
      }
  }
}

void reconnect() {
  while (!mqttClient.connected()) {
    if (DEBUG_MODE) {
      Serial.print("Intentando conexión MQTT a ");
      Serial.print(MQTT_SERVER);
      Serial.println("...");
    }
    
    String clientId = String(MQTT_CLIENT_ID) + "-" + String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      if (DEBUG_MODE) Serial.println("¡MQTT Conectado!");
      mqttClient.subscribe(TP_CTRL_IN);
      mqttClient.subscribe(TP_CTRL_OUT);
      mqttClient.subscribe(TP_CTRL_PROCESS);
    } else {
      if (DEBUG_MODE) {
        Serial.print("Fallo, rc=");
        Serial.print(mqttClient.state());
        Serial.println(" Reintentando en 5 segundos...");
      }
      delay(5000);
    }
  }
}