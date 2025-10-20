# Weed Removal Robot System

Автоматизована система для точного прополювання бур'янів на основі комп'ютерного зору та GPS-навігації.

## Особливості

- **Комп'ютерний зір**: YOLOv8 для детекції бур'янів в реальному часі
- **Точна навігація**: RTK GPS + IMU з розширеним фільтром Калмана
- **Автономне керування**: Pure Pursuit алгоритм для слідування по траєкторії
- **Веб-моніторинг**: Flask веб-інтерфейс з реальним часом
- **Телеметрія**: MQTT для передачі даних
- **Модульна архітектура**: Легко розширювана система

## Архітектура системи

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Camera    │────▶│  Detection   │────▶│   Weeding   │
│  PiCamera2  │     │    YOLOv8    │     │  Mechanism  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  RTK GPS    │────▶│    Kalman    │────▶│   Control   │
│   + IMU     │     │    Filter    │     │ Pure Pursuit│
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Telemetry   │
                    │ MQTT + Flask │
                    └──────────────┘
```

## Структура проекту

```
weed-removal-system/
├── src/
│   ├── vision/          # Модуль захоплення та обробки зображень
│   │   ├── camera.py           # PiCamera2 інтерфейс
│   │   └── preprocessor.py     # Попередня обробка зображень
│   ├── detection/       # Модуль детекції бур'янів
│   │   └── yolo_detector.py    # YOLOv8 детектор
│   ├── navigation/      # Модуль GPS-навігації
│   │   ├── gps.py              # RTK GPS інтерфейс
│   │   └── kalman_filter.py    # Розширений фільтр Калмана
│   ├── control/         # Модуль керування
│   │   ├── motor_controller.py # PWM контролер моторів
│   │   ├── pid_controller.py   # PID регулятор
│   │   └── pure_pursuit.py     # Pure Pursuit алгоритм
│   ├── weeding/         # Модуль прополювання
│   │   └── weeder.py           # Контролер механізму
│   ├── telemetry/       # Модуль телеметрії
│   │   ├── mqtt_client.py      # MQTT клієнт
│   │   └── web_server.py       # Flask веб-сервер
│   └── utils/           # Допоміжні модулі
│       ├── config_loader.py    # Завантаження конфігурації
│       └── logger.py           # Логування
├── config/
│   └── config.yaml      # Конфігураційний файл
├── web/                 # Веб-інтерфейс
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       └── js/
├── models/              # YOLOv8 моделі
├── tests/               # Тести
├── data/                # Дані та логи
├── main.py              # Головний файл програми
└── requirements.txt     # Залежності
```

## Встановлення

### 1. Системні вимоги

- Raspberry Pi 4 (рекомендовано 4GB RAM)
- Raspberry Pi Camera Module v2/v3
- u-blox ZED-F9P RTK GPS модуль
- IMU (опціонально)
- Python 3.9+

### 2. Встановлення залежностей

```bash
# Оновлення системи
sudo apt update && sudo apt upgrade -y

# Встановлення системних пакетів
sudo apt install -y python3-pip python3-venv git

# Створення віртуального середовища
python3 -m venv venv
source venv/bin/activate

# Встановлення Python пакетів
pip install -r requirements.txt
```

### 3. Налаштування апаратного забезпечення

#### Камера
```bash
# Увімкнення камери
sudo raspi-config
# Interface Options -> Camera -> Enable
```

#### GPS
```bash
# Налаштування послідовного порту
sudo raspi-config
# Interface Options -> Serial Port
# Login shell: No
# Serial hardware: Yes

# Перевірка порту GPS
ls -l /dev/ttyACM0
```

#### GPIO для моторів
Підключення за замовчуванням:
- Лівий мотор PWM: GPIO 12
- Лівий мотор DIR: GPIO 16
- Правий мотор PWM: GPIO 13
- Правий мотор DIR: GPIO 18
- Механізм прополювання: GPIO 22

### 4. Налаштування конфігурації

```bash
# Копіювання прикладу конфігурації
cp .env.example .env

# Редагування конфігурації
nano .env
nano config/config.yaml
```

### 5. Завантаження моделі YOLOv8

```bash
# Створення директорії для моделей
mkdir -p models

# Завантаження YOLOv8 моделі (приклад)
# Тренована модель для детекції бур'янів
# Розмістіть вашу натреновану модель в models/yolov8n.tflite
```

## Використання

### Запуск системи

```bash
# Активація віртуального середовища
source venv/bin/activate

# Запуск робота
python main.py

# Запуск з власною конфігурацією
python main.py --config /path/to/config.yaml
```

### Веб-інтерфейс

Після запуску системи відкрийте браузер:
```
http://<raspberry-pi-ip>:5000
```

Веб-інтерфейс надає:
- Статус робота в реальному часі
- GPS позиція та якість сигналу
- Детекції бур'янів
- Статистика роботи
- Керування роботом (старт/пауза/стоп)

### MQTT Топіки

Система публікує дані в такі топіки:
- `weed_robot/status` - статус робота
- `weed_robot/gps` - GPS дані
- `weed_robot/detections` - результати детекції
- `weed_robot/telemetry` - телеметрія

Підписка на команди:
- `weed_robot/command/#` - команди керування

## Конфігурація

### Основні параметри (config/config.yaml)

```yaml
camera:
  resolution: [1920, 1080]
  framerate: 30

detection:
  model_path: "models/yolov8n.tflite"
  confidence_threshold: 0.5

navigation:
  gps:
    port: "/dev/ttyACM0"
    baudrate: 38400

control:
  pure_pursuit:
    lookahead_distance: 1.0
    max_speed: 0.5
  pid:
    kp: 1.0
    ki: 0.1
    kd: 0.05

weeding:
  activation_duration: 0.5
  offset_y: 0.2

telemetry:
  web:
    port: 5000
  mqtt:
    broker: "localhost"
```

## Модулі системи

### 1. Vision Module
- **Camera**: Захоплення зображень з PiCamera2
- **Preprocessor**: Обробка зображень (resize, нормалізація, CLAHE)

### 2. Detection Module
- **YOLODetector**: Детекція бур'янів та культурних рослин
- Підтримка TensorFlow Lite та PyTorch
- NMS (Non-Maximum Suppression)

### 3. Navigation Module
- **GPS**: RTK GPS (u-blox ZED-F9P) з NMEA парсингом
- **KalmanFilter**: Розширений фільтр Калмана для злиття GPS+IMU

### 4. Control Module
- **MotorController**: PWM керування DC моторами
- **PIDController**: PID регулятор
- **PurePursuit**: Алгоритм слідування по траєкторії

### 5. Weeding Module
- **Weeder**: Керування механізмом прополювання
- Координація з детекцією та навігацією

### 6. Telemetry Module
- **MQTTClient**: Передача даних через MQTT
- **WebServer**: Flask веб-інтерфейс з SocketIO

## Тестування

```bash
# Запуск тестів
pytest tests/

# Тестування окремих модулів
python -m pytest tests/test_vision.py
python -m pytest tests/test_detection.py
```

## Розробка

### Додавання нових функцій

1. Створіть новий модуль в `src/`
2. Додайте конфігурацію в `config/config.yaml`
3. Інтегруйте в `main.py`
4. Додайте тести в `tests/`

### Структура коду

- Кожен модуль має чіткий інтерфейс
- Використання контекстних менеджерів
- Логування через `loguru`
- Конфігурація через YAML + .env

## Troubleshooting

### Камера не працює
```bash
# Перевірка камери
vcgencmd get_camera

# Перезавантаження камери
sudo modprobe bcm2835-v4l2
```

### GPS не підключається
```bash
# Перевірка порту
ls -l /dev/ttyACM*

# Тестування GPS
cat /dev/ttyACM0
```

### GPIO помилки
```bash
# Перевірка прав доступу
sudo usermod -a -G gpio $USER

# Перезавантаження
sudo reboot
```

## Підтримка та внесок

Якщо ви знайшли помилку або маєте пропозиції:
1. Створіть Issue
2. Зробіть Fork репозиторію
3. Створіть Pull Request

## Ліцензія

MIT License

## Автор

Дипломна робота з автоматизованої системи прополювання бур'янів

## Подяки

- YOLOv8 від Ultralytics
- FilterPy для фільтра Калмана
- Flask та SocketIO для веб-інтерфейсу
- Raspberry Pi Foundation
