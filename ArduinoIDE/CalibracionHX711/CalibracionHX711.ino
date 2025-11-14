#include <HX711.h>

#define HX711_CLK 2     // D4
#define HX711_DO 14     // D5

HX711 scale;
float calibration_factor = 0;   // Definir

void setup() {
  Serial.begin(115200);

  initHX711();
}

void loop() {
  Serial.print("Valor de lectura: \t");
  Serial.println(scale.get_value(10),0);
  delay(500);
}

void initHX711(){
  scale.begin(HX711_DO, HX711_CLK);

  Serial.print("Lectura del valor del ADC:t");
  Serial.println(scale.read());

  Serial.println("No ponga ningún objeto sobre la balanza");
  Serial.println("Destarando...");

  scale.set_scale();
  scale.tare(20);
  
  delay(1000);
  Serial.println("Coloque un peso conocido:");
}