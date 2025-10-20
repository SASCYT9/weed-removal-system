# Архітектура системи прополювання бур'янів

## Огляд системи

Система побудована за модульним принципом з чіткою ієрархією компонентів та відповідальностей.

## Діаграма компонентів

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Application (main.py)                │
│                  WeedRemovalRobot Controller                 │
└────────┬────────────────────────────────────────────────────┘
         │
    ┌────┴─────┬──────────┬──────────┬──────────┬──────────┐
    │          │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Vision │ │Detection│ │Navigation│ │Control │ │Weeding │ │Telemetry│
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

## Модулі системи

### 1. Vision Module (`src/vision/`)

**Призначення**: Захоплення та попередня обробка зображень

**Компоненти**:
- `Camera`: Інтерфейс камери PiCamera2
  - Підтримка різних роздільностей
  - Настроюваний FPS
  - Context manager для безпечної роботи

- `ImagePreprocessor`: Обробка зображень
  - Зміна розміру з збереженням співвідношення
  - CLAHE для покращення контрасту
  - Нормалізація для нейронної мережі
  - Фільтрація шумів

**Потік даних**:
```
Camera → Raw Image → Preprocessor → Normalized Image → Detection
```

### 2. Detection Module (`src/detection/`)

**Призначення**: Детекція бур'янів та культурних рослин

**Компоненти**:
- `YOLODetector`: YOLOv8 детектор
  - Підтримка TFLite та PyTorch
  - Configurable thresholds
  - NMS для видалення дублікатів
  - Фільтрація по класах

- `Detection`: Dataclass для результатів
  - Клас об'єкта
  - Впевненість детекції
  - Bounding box
  - Центр об'єкта

**Алгоритм детекції**:
```
Image → Model Inference → Raw Detections → NMS → Filtered Detections
```

### 3. Navigation Module (`src/navigation/`)

**Призначення**: Високоточна навігація з GPS та IMU

**Компоненти**:
- `GPS`: RTK GPS інтерфейс
  - NMEA протокол (GGA, RMC, VTG)
  - Асинхронне читання
  - RTKFixed/Float detection
  - Thread-safe операції

- `NavigationKalmanFilter`: Розширений фільтр Калмана
  - 6-вимірний стан (x, y, vx, vy, heading, ω)
  - Predict-Update цикл
  - Сенсорна фузія GPS+IMU
  - Адаптивна коваріація

**Цикл навігації**:
```
GPS Data → Kalman Predict → GPS Update → Filtered State → Control
     ↑                                                          │
     └──────────────────── dt ─────────────────────────────────┘
```

### 4. Control Module (`src/control/`)

**Призначення**: Керування рухом робота

**Компоненти**:
- `MotorController`: PWM контролер
  - Differential drive
  - Двонаправлене керування
  - Обмеження швидкості

- `PIDController`: PID регулятор
  - P, I, D компоненти
  - Anti-windup
  - Output limiting

- `PurePursuit`: Path following
  - Adaptive lookahead
  - Curvature calculation
  - Speed modulation

**Контрольний цикл**:
```
Path → Pure Pursuit → (v, ω) → Differential Drive → Motor PWM
         ↑                                               │
         └────────── Current Pose ──────────────────────┘
```

### 5. Weeding Module (`src/weeding/`)

**Призначення**: Активація механізму прополювання

**Компоненти**:
- `Weeder`: Контролер механізму
  - GPIO керування
  - Координація з детекцією
  - Offset compensation
  - Statistics tracking

**Логіка прополювання**:
```
Weed Detection → Position Transform → Range Check → Activate → Log
```

### 6. Telemetry Module (`src/telemetry/`)

**Призначення**: Моніторинг та управління

**Компоненти**:
- `MQTTClient`: MQTT клієнт
  - Publish/Subscribe
  - JSON serialization
  - Auto-reconnect
  - QoS support

- `WebServer`: Flask веб-сервер
  - SocketIO для реального часу
  - RESTful API
  - Responsive dashboard

**Топіки MQTT**:
```
weed_robot/
├── status          (Robot state)
├── gps            (GPS data)
├── detections     (YOLO results)
├── telemetry      (General data)
└── command/       (Control commands)
```

## Потік даних в системі

### Основний цикл (20 Hz):

```
1. Camera Capture
   ↓
2. Image Preprocessing
   ↓
3. YOLO Detection
   ↓
4. GPS Reading
   ↓
5. Kalman Filter Update
   ↓
6. Path Following (Pure Pursuit)
   ↓
7. Motor Control
   ↓
8. Weeding Activation (if weed detected)
   ↓
9. Telemetry Publishing
   ↓
   └→ Back to 1
```

## Конфігурація

### Ієрархія конфігурації:

```
config.yaml (Base) → .env (Override) → Runtime params
```

### Основні параметри:

- **Camera**: resolution, framerate, format
- **Detection**: model_path, thresholds
- **Navigation**: GPS port, Kalman parameters
- **Control**: PID gains, Pure Pursuit params
- **Weeding**: activation time, offset
- **Telemetry**: MQTT broker, Web port

## Обробка помилок

### Стратегія:

1. **Graceful degradation**: Система продовжує працювати при відмові окремих компонентів
2. **Logging**: Всі помилки логуються з контекстом
3. **Emergency stop**: Миттєва зупинка при критичних помилках
4. **Auto-recovery**: Спроби автоматичного відновлення

### Приклади:

- GPS loss → Використання last known position
- Camera failure → Зупинка детекції, продовження навігації
- MQTT disconnect → Auto-reconnect, локальне логування

## Продуктивність

### Цільові показники:

- **Update rate**: 20 Hz
- **Detection latency**: < 100 ms
- **GPS update**: 10 Hz
- **Web UI refresh**: 5 Hz

### Оптимізації:

- TensorFlow Lite для швидкої інференції
- Асинхронні I/O для GPS/MQTT
- Threading для веб-сервера
- Efficient numpy operations

## Розширення системи

### Додавання нового модуля:

1. Створити клас в `src/module_name/`
2. Додати конфігурацію в `config.yaml`
3. Інтегрувати в `main.py`
4. Додати тести в `tests/`

### Приклади розширень:

- **Obstacle avoidance**: LIDAR integration
- **Multi-robot**: Swarm coordination
- **AI planning**: Reinforcement learning
- **Crop monitoring**: Health detection
