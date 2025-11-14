#include <ESP8266WiFi.h>

#define debugMode 0

#define pi 3.14159265359

//------------  Credenciales WiFi  ------------//
#define ssid "xxxxx"
#define password "xxxxx"
//WiFiServer server(80);

//----------  Definiciones de pines  ----------//
#define Trigger 12       // D6
#define Echo 13          // D7

#define HX711_CLK  2     // D4
#define HX711_DO 14      // D5

//------------  Variables globales  -----------//
String header;
unsigned long t, d, lastTime, timeout = 2000;
float area = pi * (xx^2);  // pi*radio^2

float densidad = 1000;  // Densidad del fluido
float factor_US = 20;   // Refiere a la distancia con tanque vacio

HX711 scale;
float peso;
float calibration_factor = 0;   // Definir

float vol_diff, vol_prom, vol_US, vol_HX711, volumen;

void setup() {
  if(debugMode){
    Serial.begin(115200);
  }

  initWiFi();
  initUS();
  initHX711();
}

void loop() {
  // put your main code here, to run repeatedly:

}

void initWiFi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while(WiFi.status() != WL_CONNECTED){
    delay(500);
  }

  if(debugMode){
    Serial.println("");
    Serial.println("Conectado a la red.");
    Serial.print("Dirección IP: "); Serial.println(WiFi.localIP());
  }
}

void initUS(){
  pinMode(Trigger, OUTPUT); //pin como salida
  pinMode(Echo, INPUT);  //pin como entrada
  digitalWrite(Trigger, LOW);//Inicializamos el pin con 0

  if(debugMode){
    Serial.println("Sensor Ultrasonico inicializado.");
  }
}

void initHX711(){
  scale.begin(HX711_DO, HX711_CLK);
  scale.tare(20);
  scale.set_scale(calibration_factor);

  if(debugMode){
    Serial.println("Celda de carga inicializada.");
  }
}

void measureUS(){
  digitalWrite(Trigger, HIGH);
  delayMicroseconds(10);          //Enviamos un pulso de 10us
  digitalWrite(Trigger, LOW);

  t = pulseIn(Echo, HIGH); //obtenemos el ancho del pulso
  d = t / 58.4;             //escalamos el tiempo a una distancia en cm

  vol_US = (factor_US - d) * area;

  if(debugMode){
    Serial.print("Volumen US: "); Serial.println(vol_US);
  }
}

void measureHX711(){
  peso = scale.get_units(20)

  vol_HX711 = (peso / 9.81) / densidad;

  if(debugMode){
    Serial.print("Volumen HX711: "); Serial.println(vol_HX711);
  }
}

void sendVolumen(){
  vol_diff = vol_US - vol_HX711;
  vol_prom = (vol_US + vol_HX711) / 2;
  volumen = xxxxx;

  if(debugMode){
    Serial.print("Volumen diferencial: "); Serial.println(vol_diff);
    Serial.print("Volumen promedio: "); Serial.println(vol_prom);
    Serial.print("Dato enviado: "); Serial.println(volumen);
  }

  /*
    Logica para enviar datos
  */
}