/*
 * -----------------------------------------------------------------------
 * SISTEMA INTEGRAL SCADA - WEMOS D1 R2 (VERSIÓN ROB TILLAART RESTAURADA)
 * -----------------------------------------------------------------------
 * Librería Específica: https://github.com/RobTillaart/MAX6675
 * Lógica:
 * 1. Constructor: (CS, SO, SCK).
 * 2. Setup: thermocouple.begin().
 * 3. Loop: int status = thermocouple.read() -> getTemperature().
 * -----------------------------------------------------------------------
 */

#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MAX6675.h>  // Librería Rob Tillaart
#include <Adafruit_ADS1X15.h>
#include <HX711.h> 

// =========================================================
// 1. CONFIGURACIÓN
// =========================================================
#define DEBUG_MODE 0     

// ⚠️ ATENCIÓN: VERIFICA QUE ESTA IP SEA LA DE TU BROKER
#define MQTT_SERVER "192.168.1.250" 
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "Wemos_UC_SO"

// --- TEMPORIZADORES ---
const unsigned long INTERVAL_METEO   = 15 * 60 * 1000; // 15 Minutos
const unsigned long INTERVAL_PROCESS = 5000;          // 5 Segundos
bool firstRun = true; // Bandera para primer envío

// --- GEOMETRÍA DEL TANQUE (Para cálculo de volumen) ---
// Ajustar estos valores según las medidas reales del tanque cilíndrico
const float TANK_RADIUS_CM = 10.0;   // Radio interno del tanque
const float SENSOR_HEIGHT_CM = 30.0; // Distancia desde el sensor hasta el fondo (Tanque vacío)

// =========================================================
// 2. MAPEO DE PINES
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

// A futuro, no hay pines suficientes
/*
#define US_OUT_TRIG      xx
#define US_OUT_ECHO      xx

#define HX_OUT_DT        xx
#define HX_OUT_SCK       xx
*/

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
//HX711 scaleOut;

struct State {
  float temp_amb;           // Se publica en environment
  float hum_amb;            // Se publica en environment
  float pres_amb;           // Se publica en environment

  float radiation;          // Se publica en radiation
  float temp_int;           // Se publica en temperature

  float lvl_in_weight;      // Peso directo (kg)
  float lvl_in_dist;        // Distancia directa (cm)
  float lvl_in;             // VOLUMEN CALCULADO (ml) - Promedio fusionado

  float lvl_out_weight;
  float lvl_out_dist;   
  float lvl_out;            // VOLUMEN CALCULADO (ml) - Promedio fusionado

  float chamber_level;     // Se publica en chamber_level

  bool valve_in_state;
  bool valve_out_state;
  bool process_active;
} sysState;

unsigned long lastMeteoTime = 0;
unsigned long lastProcessTime = 0;

// Constantes
const float PYR_GAIN = 0.0078125;
const float PYR_CAL = 70.9e-3;
const float SCALE_CAL_IN = 2280.0;
const float SCALE_CAL_OUT = 2280.0;
const float PI_VAL = 3.14159265359;

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
  
  sysState.process_active = false;

  sysState.valve_in_state = false;
  sysState.valve_out_state = false;

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

  // --- TAREA DE REPORTE ---
  if ((now - lastMeteoTime > INTERVAL_METEO) || firstRun) {
    lastMeteoTime = now;
    
    if (DEBUG_MODE) Serial.println(">>> EJECUTANDO TAREA DE REPORTE <<<");
    
    measureEnvironment();
    measureRadiation();
    
    pubEnvironment();
    pubRadiation();
    
    if (!sysState.process_active) {
       measureInternalTemp();
       measureLevelIn();
       measureLevelOut();
       measureChamberLevel();

       pubInternalTemp();
       pubLevelIn();
       pubLevelOut(); 
       //pubChamberLevel();
    }
    
    if (firstRun) {
        if (DEBUG_MODE) Serial.println(">>> Primer envío completado <<<");
        firstRun = false;
    }
  }

  // --- TAREA DE PROCESO ---
  if (sysState.process_active) {
    if (now - lastProcessTime > INTERVAL_PROCESS) {
      lastProcessTime = now;
      if (DEBUG_MODE) Serial.println(">>> EJECUTANDO TAREA DE PROCESO <<<");
      
      measureInternalTemp();
      measureLevelIn();
      measureLevelOut();
      measureChamberLevel();

      runProcessLogic();

      pubInternalTemp();
      pubLevelIn();
      pubLevelOut();
      //pubChamberLevel();
    }
  }
}

// =========================================================
// 6. LÓGICA DE PROCESO
// =========================================================
void runProcessLogic() {
  if (sysState.process_active) {
    // Placeholder
  } else{
    return;
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

  if (DEBUG_MODE) Serial.println("Iniciando MAX6675 (Rob Tillaart)...");
  thermocouple.begin(); 

  if (DEBUG_MODE) Serial.println("Iniciando Ultrasonico In...");
  pinMode(US_IN_TRIG, OUTPUT);
  pinMode(US_IN_ECHO, INPUT);
  digitalWrite(US_IN_TRIG, LOW);

  // --- HX711 COMENTADO ---
  /*
  if (DEBUG_MODE) Serial.println("Iniciando HX711 In...");
  scaleIn.begin(HX_IN_DT, HX_IN_SCK);
  scaleIn.set_scale(SCALE_CAL_IN);
  scaleIn.tare();
  */

  // A futuro, no implementado aun
  /*
  if (DEBUG_MODE) Serial.println("Iniciando Ultrasonico Out...");
  pinMode(US_OUT_TRIG, OUTPUT);
  pinMode(US_OUT_ECHO, INPUT);
  digitalWrite(US_OUT_TRIG, LOW);

  if (DEBUG_MODE) Serial.println("Iniciando HX711 Out...");
  scaleIn.begin(HX_OUT_DT, HX_OUT_SCK);
  scaleIn.set_scale(SCALE_CAL_OUT);
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
  sysState.radiation = -1.0;
  if (DEBUG_MODE) Serial.printf("Rad: %.2f\n", sysState.radiation);
}

void measureInternalTemp() {
  int status = thermocouple.read();
  
  if (status == STATUS_OK) {
    sysState.temp_int = thermocouple.getTemperature();
  } else {
    sysState.temp_int = -1.0;
    if (DEBUG_MODE) {
        Serial.print("MAX6675 Error: "); Serial.println(status);
    }
  }
  
  if (DEBUG_MODE) Serial.printf("Temp Int: %.2f\n", sysState.temp_int);
}

void measureLevelIn() {
  float vol_ultrasonico = -1.0;
  float vol_peso = -1.0;

  // --- 1. MEDICIÓN ULTRASONIDO (Distancia) ---
  digitalWrite(US_IN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(US_IN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(US_IN_TRIG, LOW);
  long dur = pulseIn(US_IN_ECHO, HIGH); // 30ms timeout
  
  if (dur == 0) {
    sysState.lvl_in_dist = -1.0;
  } else {
    sysState.lvl_in_dist = dur * 0.034 / 2.0;
    // CÁLCULO VOLUMEN (Cilindro)
    // Altura de agua = Altura Sensor - Distancia Medida
    float water_height = SENSOR_HEIGHT_CM - sysState.lvl_in_dist;
    if (water_height < 0) water_height = 0;
    
    // Vol = Pi * r^2 * h
    vol_ultrasonico = PI_VAL * (TANK_RADIUS_CM * TANK_RADIUS_CM) * water_height; 
  }

  // --- 2. MEDICIÓN HX711 (Peso) ---
  /*
  if (scaleIn.is_ready()) {
    sysState.lvl_in_weight = scaleIn.get_units(1);
    // CÁLCULO VOLUMEN (Peso)
    // Asumimos 1g = 1ml (Densidad agua aprox) -> 1kg = 1000ml
    if (sysState.lvl_in_weight < 0) sysState.lvl_in_weight = 0; // Filtrar tara negativa
    vol_peso = sysState.lvl_in_weight * 1000.0; 
  } else {
    sysState.lvl_in_weight = -1.0;
  }
  */
  sysState.lvl_in_weight = -1.0; // Placeholder

  // --- 3. FUSIÓN DE SENSORES (PROMEDIO) ---
  if (vol_ultrasonico >= 0 && vol_peso >= 0) {
    // Ambos sensores OK -> Promedio
    sysState.lvl_in = (vol_ultrasonico + vol_peso) / 2.0;
  } else if (vol_ultrasonico >= 0) {
    // Solo ultrasonido OK
    sysState.lvl_in = vol_ultrasonico;
  } else if (vol_peso >= 0) {
    // Solo peso OK
    sysState.lvl_in = vol_peso;
  } else {
    // Ninguno OK
    sysState.lvl_in = -1.0;
  }
  
  if (DEBUG_MODE) Serial.printf("Lvl In: Dist=%.1fcm Peso=%.2fkg Vol=%.0fml\n", 
                                sysState.lvl_in_dist, sysState.lvl_in_weight, sysState.lvl_in);
}

void measureLevelOut() {
  float vol_ultrasonico = -1.0;
  float vol_peso = -1.0;

  // --- 1. MEDICIÓN ULTRASONIDO (Distancia) ---
  /* digitalWrite(US_OUT_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(US_OUT_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(US_OUT_TRIG, LOW);
  long dur = pulseIn(US_OUT_ECHO, HIGH);
  
  if (dur == 0) {
    sysState.lvl_out_dist = -1.0;
  } else {
    sysState.lvl_out_dist = dur * 0.034 / 2.0;
    // CÁLCULO VOLUMEN
    float water_height = SENSOR_HEIGHT_CM - sysState.lvl_out_dist;
    if (water_height < 0) water_height = 0;
    vol_ultrasonico = PI_VAL * (TANK_RADIUS_CM * TANK_RADIUS_CM) * water_height; 
  }
  */
  sysState.lvl_out_dist = -1.0; // Placeholder

  // --- 2. MEDICIÓN HX711 (Peso) ---
  /*
  if (scaleOut.is_ready()) {
    sysState.lvl_out_weight = scaleOut.get_units(1);
    if (sysState.lvl_out_weight < 0) sysState.lvl_out_weight = 0;
    vol_peso = sysState.lvl_out_weight * 1000.0; 
  } else {
    sysState.lvl_out_weight = -1.0;
  }
  */
  sysState.lvl_out_weight = -1.0; // Placeholder

  // --- 3. FUSIÓN DE SENSORES (PROMEDIO) ---
  if (vol_ultrasonico >= 0 && vol_peso >= 0) {
    sysState.lvl_out = (vol_ultrasonico + vol_peso) / 2.0;
  } else if (vol_ultrasonico >= 0) {
    sysState.lvl_out = vol_ultrasonico;
  } else if (vol_peso >= 0) {
    sysState.lvl_out = vol_peso;
  } else {
    sysState.lvl_out = -1.0;
  }
}

void measureChamberLevel(){
  //place holder
  sysState.chamber_level = -1.0;
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
  char msg[50];
  // Formato CSV extendido: Peso(kg), Distancia(cm), Volumen(ml)
  snprintf(msg, sizeof(msg), "%.2f,%.2f,%.0f", sysState.lvl_in_weight, sysState.lvl_in_dist, sysState.lvl_in);
  mqttClient.publish(TP_MEAS_LVL_IN, msg);
}

void pubLevelOut() {
  char msg[50];
  // Formato CSV extendido: Peso(kg), Distancia(cm), Volumen(ml)
  snprintf(msg, sizeof(msg), "%.2f,%.2f,%.0f", sysState.lvl_out_weight, sysState.lvl_out_dist, sysState.lvl_out);
  mqttClient.publish(TP_MEAS_LVL_OUT, msg);
}

void pubChamberLevel() {
  char msg[15];
  snprintf(msg, sizeof(msg), "%.3f", sysState.chamber_level);
  mqttClient.publish(TP_MEAS_CHAMBER, msg);
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