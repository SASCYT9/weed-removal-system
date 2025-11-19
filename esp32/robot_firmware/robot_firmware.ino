/*
 * ===================================================================
 * Повний код для робота ESP32 (WEMOS D32)
 * НОВА ВЕРСІЯ: КЕРУВАННЯ ЧЕРЕЗ WEB-СЕРВЕР (WiFi)
 *
 * *** ОНОВЛЕННЯ: Використовуємо analogWrite() замість ledcSetup(),
 * *** щоб обійти помилку компілятора "ledcSetup was not declared".
 * ===================================================================
 *
 * * ПЕРЕД ЗАВАНТАЖЕННЯМ:
 * 1. Встановіть бібліотеки: 'TinyGPSPlus', 'ESPAsyncWebServer', 'AsyncTCP'
 * 2. Перевірте всі підключення.
 */

// --- Підключення Бібліотек ---
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <HardwareSerial.h>
#include <TinyGPS++.h>

// --- Ваші дані WiFi ---
const char* ssid = "ASUS_2g";
const char* password = "Lizathebest";

// --- Об'єкти ---
AsyncWebServer server(80); // Сервер на 80 порту
AsyncWebSocket ws("/ws");  // WebSocket для "радару"
TinyGPSPlus gps;
HardwareSerial Serial2(2);

// ===================================
// --- РОЗПІНОВКА (GPIO НОМЕРИ) ---
// ===================================
const int MOTOR_A_IN1 = 26; // Пін D0 -> IN1
const int MOTOR_A_IN2 = 25; // Пін D1 -> IN2
const int MOTOR_A_ENA = 21; // Пін D7 -> ENA (Швидкість A)
const int MOTOR_B_IN3 = 18; // Пін D5 -> IN3
const int MOTOR_B_IN4 = 19; // Пін D6 -> IN4
const int MOTOR_B_ENB = 22; // Пін D8 -> ENB (Швидкість B)
const int ULTRA_TRIG_PIN = 4;  // Пін D4 -> Trig
const int ULTRA_ECHO_PIN = 36; // Пін A0 -> Echo
const int GPS_RX_PIN = 16; // Пін D3 (до TXD на GPS)
const int GPS_TX_PIN = 17; // Пін D2 (до RXD на GPS)

// --- Налаштування ШІМ (PWM) ---
// Ми більше не використовуємо ledcSetup. 
// analogWrite() використовує 8-біт (0-255) та 5000 Гц за замовчуванням.

// *** Змінна для швидкості (тепер не константа!) ***
volatile int motorSpeed = 200; // (0-255)

// --- Змінні для таймерів ---
unsigned long sensorReadTimer = 0;
long lastDistance = 0;
String lastGpsString = "GPS: Пошук...";

// ===================================
// ---         WEB-СТОРІНКА        ---
// ===================================
// (HTML, CSS та JavaScript в одному рядку)
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <title>ESP32 Robot Control</title>
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
  <style>
    body { font-family: Arial, sans-serif; background: #2c2c2c; color: #eee; text-align: center; margin: 0; padding: 0; }
    h1 { margin-top: 15px; }
    .container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    #joystick-container { position: relative; width: 200px; height: 200px; background: #444; border-radius: 50%; margin: 20px; }
    #joystick-knob { position: absolute; width: 80px; height: 80px; background: #888; border-radius: 50%; left: 60px; top: 60px; cursor: pointer; }
    .slider-container { margin: 20px; }
    #speed-slider { width: 300px; -webkit-appearance: none; appearance: none; height: 15px; background: #555; border-radius: 5px; outline: none; }
    #speed-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 30px; height: 30px; background: #00bcd4; border-radius: 50%; cursor: pointer; }
    .info { margin-top: 20px; }
    #radar-container { position: relative; width: 300px; height: 300px; background: #000; border-radius: 50%; border: 2px solid #0f0; margin: 20px auto; overflow: hidden; }
    #radar-sweep { position: absolute; width: 50%; height: 50%; left: 50%; top: 50%; background: linear-gradient(0deg, rgba(0,255,0,0.5) 0%, rgba(0,255,0,0) 100%); transform-origin: 0% 0%; animation: sweep 2s linear infinite; }
    @keyframes sweep { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .radar-grid { position: absolute; width: 100%; height: 100%; border-radius: 50%; box-sizing: border-box; }
    .grid1 { border: 1px dashed #0f0; }
    .grid2 { width: 66.66%; height: 66.66%; top: 16.67%; left: 16.67%; }
    .grid3 { width: 33.33%; height: 33.33%; top: 33.33%; left: 33.33%; }
    #distance-text { position: absolute; top: 10px; left: 10px; color: #0f0; font-size: 1.2em; }
    #gps-text { font-size: 1.1em; color: #ffeb3b; }
  </style>
</head>
<body>
  <div class="container">
    <h1>ESP32 Robot Control</h1>
    <div id="joystick-container">
      <div id="joystick-knob"></div>
    </div>
    <div class="slider-container">
      Speed: <span id="speed-value">200</span>
      <input type="range" min="100" max="255" value="200" id="speed-slider" oninput="updateSpeed(this.value)">
    </div>
    <div class="info">
      <div id="radar-container">
        <div id="radar-sweep"></div>
        <div class="radar-grid grid1"></div>
        <div class="radar-grid grid2 grid1"></div>
        <div class="radar-grid grid3 grid1"></div>
        <div id="distance-text">... cm</div>
      </div>
      <div id="gps-text">GPS: Connecting...</div>
    </div>
  </div>
  <script>
    let ws = new WebSocket("ws://" + window.location.hostname + "/ws");
    let joystickKnob = document.getElementById("joystick-knob");
    let joystickContainer = document.getElementById("joystick-container");
    let speedValue = document.getElementById("speed-value");
    let distText = document.getElementById("distance-text");
    let gpsText = document.getElementById("gps-text");
    let dragging = false;
    let currentCommand = "stop";

    ws.onmessage = function(event) {
      let data = JSON.parse(event.data);
      if (data.distance !== undefined) {
        distText.textContent = data.distance + " cm";
      }
      if (data.gps !== undefined) {
        gpsText.textContent = data.gps;
      }
    };

    function sendCommand(cmd) {
      if (cmd !== currentCommand) {
        fetch("/control?cmd=" + cmd);
        currentCommand = cmd;
      }
    }

    function updateSpeed(val) {
      speedValue.textContent = val;
      fetch("/speed?value=" + val);
    }

    function handleMove(x, y) {
      let rect = joystickContainer.getBoundingClientRect();
      let centerX = rect.width / 2;
      let centerY = rect.height / 2;
      let relX = x - rect.left - centerX;
      let relY = y - rect.top - centerY;
      let angle = Math.atan2(relY, relX) * 180 / Math.PI;
      let distance = Math.sqrt(relX * relX + relY * relY);

      if (distance < 30) { // Dead zone
        joystickKnob.style.left = "60px";
        joystickKnob.style.top = "60px";
        sendCommand("stop");
        return;
      }

      // Constrain knob
      let maxDist = centerX - 40; // 40 = knob radius
      let constrainedX = Math.min(maxDist, Math.max(-maxDist, relX));
      let constrainedY = Math.min(maxDist, Math.max(-maxDist, relY));
      joystickKnob.style.left = (constrainedX + centerX - 40) + "px";
      joystickKnob.style.top = (constrainedY + centerY - 40) + "px";

      // Determine command
      if (angle > -135 && angle < -45) sendCommand("forward");
      else if (angle > 45 && angle < 135) sendCommand("backward");
      else if (angle >= 135 || angle <= -135) sendCommand("left");
      else if (angle >= -45 && angle <= 45) sendCommand("right");
    }

    function handleEnd() {
      if (dragging) {
        dragging = false;
        joystickKnob.style.left = "60px";
        joystickKnob.style.top = "60px";
        sendCommand("stop");
      }
    }

    // Mouse events
    joystickKnob.addEventListener("mousedown", () => dragging = true);
    document.addEventListener("mouseup", handleEnd);
    document.addEventListener("mousemove", (e) => {
      if (dragging) handleMove(e.clientX, e.clientY);
    });

    // Touch events
    joystickKnob.addEventListener("touchstart", (e) => {
      dragging = true;
      e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchend", (e) => {
      handleEnd();
      e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchmove", (e) => {
      if (dragging) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
      }
    }, { passive: false });

  </script>
</body>
</html>
)rawliteral";

// ===================================
// --- ФУНКЦІЇ КЕРУВАННЯ МОТОРАМИ ---
// ===================================
// (Тепер використовуємо analogWrite замість ledcWrite)

void stopMotors() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, LOW);
  digitalWrite(MOTOR_B_IN3, LOW);
  digitalWrite(MOTOR_B_IN4, LOW);
  // Встановлюємо швидкість 0
  analogWrite(MOTOR_A_ENA, 0);
  analogWrite(MOTOR_B_ENB, 0);
}

void moveForward() {
  digitalWrite(MOTOR_A_IN1, HIGH);
  digitalWrite(MOTOR_A_IN2, LOW);
  digitalWrite(MOTOR_B_IN3, HIGH);
  digitalWrite(MOTOR_B_IN4, LOW);
  // Встановлюємо швидкість
  analogWrite(MOTOR_A_ENA, motorSpeed);
  analogWrite(MOTOR_B_ENB, motorSpeed);
}

void moveBackward() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, HIGH);
  digitalWrite(MOTOR_B_IN3, LOW);
  digitalWrite(MOTOR_B_IN4, HIGH);
  // Встановлюємо швидкість
  analogWrite(MOTOR_A_ENA, motorSpeed);
  analogWrite(MOTOR_B_ENB, motorSpeed);
}

void turnLeft() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, HIGH);
  digitalWrite(MOTOR_B_IN3, HIGH);
  digitalWrite(MOTOR_B_IN4, LOW);
  // Встановлюємо швидкість
  analogWrite(MOTOR_A_ENA, motorSpeed);
  analogWrite(MOTOR_B_ENB, motorSpeed);
}

void turnRight() {
  digitalWrite(MOTOR_A_IN1, HIGH);
  digitalWrite(MOTOR_A_IN2, LOW);
  digitalWrite(MOTOR_B_IN3, LOW);
  digitalWrite(MOTOR_B_IN4, HIGH);
  // Встановлюємо швидкість
  analogWrite(MOTOR_A_ENA, motorSpeed);
  analogWrite(MOTOR_B_ENB, motorSpeed);
}

// ===================================
// --- ФУНКЦІЇ ДАТЧИКІВ ---
// ===================================
long getDistance() {
  digitalWrite(ULTRA_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRA_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRA_TRIG_PIN, LOW);
  long duration = pulseIn(ULTRA_ECHO_PIN, HIGH);
  long distance = (duration * 0.0343) / 2;
  return distance;
}

void readGPS() {
  while (Serial2.available() > 0) {
    if (gps.encode(Serial2.read())) {
      if (gps.location.isValid()) {
        lastGpsString = "GPS: ";
        lastGpsString += String(gps.location.lat(), 6);
        lastGpsString += ", ";
        lastGpsString += String(gps.location.lng(), 6);
        lastGpsString += " | Sats: ";
        lastGpsString += String(gps.satellites.value());
      } else {
        lastGpsString = "GPS: Пошук супутників...";
      }
    }
  }
}

// ===================================
// ---   НАЛАШТУВАННЯ СЕРВЕРА    ---
// ===================================

// Коли клієнт підключається до WebSocket
void onWsEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_CONNECT) {
    Serial.println("WebSocket клієнт підключився");
    // Відправляємо поточні дані
    String json = "{\"distance\":" + String(lastDistance) + ", \"gps\":\"" + lastGpsString + "\"}";
    client->text(json);
  } else if (type == WS_EVT_DISCONNECT) {
    Serial.println("WebSocket клієнт відключився");
  }
}

void setupServer() {
  // Налаштовуємо WebSocket
  ws.onEvent(onWsEvent);
  server.addHandler(&ws);

  // Надаємо головну HTML сторінку
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send_P(200, "text/html", index_html);
  });

  // Обробник для команд керування
  server.on("/control", HTTP_GET, [](AsyncWebServerRequest *request) {
    if (request->hasParam("cmd")) {
      String cmd = request->getParam("cmd")->value();
      if (cmd == "forward") moveForward();
      else if (cmd == "backward") moveBackward();
      else if (cmd == "left") turnLeft();
      else if (cmd == "right") turnRight();
      else if (cmd == "stop") stopMotors();
      request->send(200, "text/plain", "OK");
    } else {
      request->send(400, "text/plain", "Missing cmd");
    }
  });

  // Обробник для слайдера швидкості
  server.on("/speed", HTTP_GET, [](AsyncWebServerRequest *request) {
    if (request->hasParam("value")) {
      motorSpeed = request->getParam("value")->value().toInt();
      if (motorSpeed < 100) motorSpeed = 100; // Мінімальна швидкість
      if (motorSpeed > 255) motorSpeed = 255;
      request->send(200, "text/plain", "Speed set to " + String(motorSpeed));
    } else {
      request->send(400, "text/plain", "Missing value");
    }
  });
}

// ===================================
// ---         SETUP         ---
// ===================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Запуск Робота з WiFi (Версія analogWrite) ---");

  // --- Налаштування Моторів (PWM) ---
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN3, OUTPUT);
  pinMode(MOTOR_B_IN4, OUTPUT);
  
  // ENA/ENB піни тепер також просто OUTPUT для analogWrite
  pinMode(MOTOR_A_ENA, OUTPUT);
  pinMode(MOTOR_B_ENB, OUTPUT);

  // *** Ми ВИДАЛИЛИ ledcSetup() та ledcAttachPin() ***
  
  stopMotors(); // Починаємо з вимкненими моторами
  Serial.println("Мотори (analogWrite) налаштовані.");

  // --- Налаштування ультрасоніка ---
  pinMode(ULTRA_TRIG_PIN, OUTPUT);
  pinMode(ULTRA_ECHO_PIN, INPUT);
  Serial.println("Ультрасонік налаштований.");

  // --- Запуск Serial2 для GPS ---
  Serial2.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("GPS Serial2 запущено.");

  // --- Підключення до WiFi ---
  Serial.print("Підключення до ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED && attempt < 20) {
    delay(500);
    Serial.print(".");
    attempt++;
  }
  if(WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi підключено!");
    Serial.print("IP адреса: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nНе вдалося підключитися до WiFi. Перезавантаження...");
    delay(1000);
    ESP.restart();
  }

  // --- Налаштування та запуск сервера ---
  setupServer();
  server.begin();
  Serial.println("Web-сервер запущено!");
}

// ===================================
// ---         LOOP         ---
// ===================================
void loop() {
  unsigned long currentTime = millis();

  // Читаємо GPS постійно
  readGPS();

  // --- 2. Зчитування Датчиків та відправка (кожні 250 мс) ---
  if (currentTime - sensorReadTimer > 250) {
    sensorReadTimer = currentTime;

    // Читаємо Ультрасонік
    lastDistance = getDistance();

    // Створюємо JSON рядок
    String json = "{\"distance\":" + String(lastDistance) + ", \"gps\":\"" + lastGpsString + "\"}";
    
    // Відправляємо всім підключеним клієнтам WebSocket
    ws.textAll(json);
  }
}