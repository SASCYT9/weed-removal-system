#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <TinyGPS++.h>

/*
 * ----------------------------------------------------
 * РОЗПІНОВКА ДЛЯ ПЛАТИ WEMOS D32 (та аналогічних)
 * ----------------------------------------------------
 */

// --- Керування Моторами (L298N) ---
const int MOTOR_A_IN1 = 26; // Пін D0 -> IN1
const int MOTOR_A_IN2 = 25; // Пін D1 -> IN2
const int MOTOR_B_IN3 = 18; // Пін D5 -> IN3
const int MOTOR_B_IN4 = 19; // Пін D6 -> IN4

// --- Ультразвуковий Датчик (HC-SR04) ---
const int ULTRA_TRIG_PIN = 4;  // Пін D4 -> Trig
const int ULTRA_ECHO_PIN = 36; // Пін A0 -> Echo (це ADC1_CH0, пін тільки для входу)

// --- GPS-модуль (UART / Serial) ---
const int GPS_RX_PIN = 16; // Пін D3 (підключений до TXD на GPS)
const int GPS_TX_PIN = 17; // Пін D2 (підключений до RXD на GPS)
HardwareSerial Serial2(2); // Використовуємо другий апаратний Serial

// --- Гіроскоп/Акселерометр (MPU-6050, I2C) ---
const int I2C_SDA_PIN = 21; // Пін D7 -> SDA
const int I2C_SCL_PIN = 22; // Пін D8 -> SCL

// --- Об'єкти та глобальні змінні ---
Adafruit_MPU6050 mpu;
TinyGPSPlus gps;
JsonDocument doc; // Для прийому та відправки JSON

unsigned long lastReportTime = 0;
const long reportInterval = 1000; // Відправляти звіт кожну секунду

const int MIN_DISTANCE_CM = 20; // Мінімальна дистанція для авто-стопу

// --- Прототипи функцій ---
void processCommand(JsonDocument& doc);
void moveRobot(String direction);
float getDistance();
void sendStatusReport();

void setup() {
  // Ініціалізація основного Serial для зв'язку з RPi
  Serial.begin(115200);
  
  // Ініціалізація I2C для MPU-6050
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  if (!mpu.begin()) {
    Serial.println("{\"status\":\"error\", \"message\":\"Failed to find MPU6050 chip\"}");
    // while (1) { delay(10); } // Можна зупинити виконання, якщо MPU критично важливий
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // Ініціалізація Serial2 для GPS
  Serial2.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  // Налаштування пінів моторів
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN3, OUTPUT);
  pinMode(MOTOR_B_IN4, OUTPUT);

  // Налаштування пінів ультразвукового датчика
  pinMode(ULTRA_TRIG_PIN, OUTPUT);
  pinMode(ULTRA_ECHO_PIN, INPUT);

  Serial.println("{\"status\":\"ready\", \"message\":\"ESP32 Full-Sensor Suite Initialized\"}");
}

void loop() {
  // 1. Перевірка команд від Raspberry Pi
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    DeserializationError error = deserializeJson(doc, input);
    if (error) {
      Serial.print(F("{\"status\":\"error\", \"message\":\"deserializeJson() failed: "));
      Serial.print(error.c_str());
      Serial.println(F("\"}"));
    } else {
      processCommand(doc);
    }
  }

  // 2. Автономна зупинка при виявленні перешкоди
  float distance = getDistance();
  if (distance > 0 && distance < MIN_DISTANCE_CM) {
    moveRobot("stop");
  }

  // 3. Читання даних з GPS
  while (Serial2.available() > 0) {
    gps.encode(Serial2.read());
  }

  // 4. Відправка звіту по таймеру
  if (millis() - lastReportTime >= reportInterval) {
    sendStatusReport();
    lastReportTime = millis();
  }
}

// Обробка вхідних команд
void processCommand(JsonDocument& doc) {
  const char* command = doc["command"];
  if (command) {
    if (strcmp(command, "move") == 0) {
      String direction = doc["direction"];
      moveRobot(direction);
    }
    // Тут можна додати інші команди, наприклад "weed" для серво
  }
}

// Керування рухом робота
void moveRobot(String direction) {
  if (direction == "forward") {
    digitalWrite(MOTOR_A_IN1, HIGH);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, HIGH);
    digitalWrite(MOTOR_B_IN4, LOW);
  } else if (direction == "backward") {
    digitalWrite(MOTOR_A_IN1, LOW);
    digitalWrite(MOTOR_A_IN2, HIGH);
    digitalWrite(MOTOR_B_IN3, LOW);
    digitalWrite(MOTOR_B_IN4, HIGH);
  } else if (direction == "left") {
    digitalWrite(MOTOR_A_IN1, LOW);
    digitalWrite(MOTOR_A_IN2, HIGH);
    digitalWrite(MOTOR_B_IN3, HIGH);
    digitalWrite(MOTOR_B_IN4, LOW);
  } else if (direction == "right") {
    digitalWrite(MOTOR_A_IN1, HIGH);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, LOW);
    digitalWrite(MOTOR_B_IN4, HIGH);
  } else { // stop
    digitalWrite(MOTOR_A_IN1, LOW);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, LOW);
    digitalWrite(MOTOR_B_IN4, LOW);
  }
}

// Отримання дистанції з HC-SR04
float getDistance() {
  digitalWrite(ULTRA_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRA_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRA_TRIG_PIN, LOW);
  
  long duration = pulseIn(ULTRA_ECHO_PIN, HIGH);
  float distance = duration * 0.034 / 2;
  return distance;
}

// Відправка звіту з даними всіх сенсорів
void sendStatusReport() {
  JsonDocument report;
  
  // Дані з MPU-6050
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  JsonObject imu_data = report.createNestedObject("imu");
  JsonObject accel = imu_data.createNestedObject("accel");
  accel["x"] = a.acceleration.x;
  accel["y"] = a.acceleration.y;
  accel["z"] = a.acceleration.z;
  JsonObject gyro = imu_data.createNestedObject("gyro");
  gyro["x"] = g.gyro.x;
  gyro["y"] = g.gyro.y;
  gyro["z"] = g.gyro.z;

  // Дані з GPS
  JsonObject gps_data = report.createNestedObject("gps");
  if (gps.location.isValid()) {
    gps_data["lat"] = gps.location.lat();
    gps_data["lng"] = gps.location.lng();
    gps_data["sats"] = gps.satellites.value();
  } else {
    gps_data["lat"] = 0;
    gps_data["lng"] = 0;
    gps_data["sats"] = 0;
  }

  // Дані з ультразвукового датчика
  report["distance_cm"] = getDistance();

  // Відправка JSON на Raspberry Pi
  serializeJson(report, Serial);
  Serial.println();
}
