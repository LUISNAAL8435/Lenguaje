// ================================================
// CÓDIGO ARDUINO/ESP32 - GENERADO AUTOMÁTICAMENTE
// ================================================

#include <Arduino.h>

// --- VARIABLES GLOBALES ---
int a;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Sistema Arduino iniciado");
  
  a = 0;
  pinMode(12, OUTPUT);
  pinMode(14, INPUT);
  while (true) {
    if (true) {
      int t2 = digitalRead(14);
      bool t3 = (t2 == HIGH);
      if (t3) {
        bool t4 = (a == 0);
        if (t4) {
          digitalWrite(12, HIGH);
          a = 1;
        } else {
          digitalWrite(12, LOW);
          a = 0;
        }
      }
    }
  }
}

void loop() {
  // Código repetitivo aquí
  delay(100);
}