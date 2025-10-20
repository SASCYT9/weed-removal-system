# Режим Розробки (Development Mode)

## 📱 Тестування БЕЗ Raspberry Pi

Цей проект тепер підтримує **повне тестування на звичайному ПК/ноутбуці** без необхідності мати Raspberry Pi!

### ✨ Можливості

- ✅ **Камера ноутбука** - використовуйте вбудовану webcam
- ✅ **Камера смартфона** - підключіть телефон як IP-камеру
- ✅ **Відеофайли** - тестуйте на записаних відео
- ✅ **Зображення** - завантажте фото та тестуйте детекцію
- ✅ **Симуляція GPS** - віртуальний GPS з рухом
- ✅ **Симуляція моторів** - тестування керування
- ✅ **Симуляція сенсорів** - всі функції без апаратури

---

## 🚀 Швидкий Старт

### 1. Увімкнути Режим Розробки

Відкрийте `config/config.yaml` і встановіть:

```yaml
development:
  enabled: true  # ✅ Увімкнути режим розробки
  camera_source: "webcam"  # Джерело камери
  simulate_gps: true
  simulate_motors: true
  simulate_sensors: true
```

### 2. Запустити Систему

```powershell
python main.py
```

Система автоматично:
- ✅ Використає камеру ноутбука замість PiCamera
- ✅ Симулює GPS (віртуальний рух по Києву)
- ✅ Симулює мотори (виводить команди в лог)
- ✅ Симулює weeder (рахує активації)

### 3. Відкрити PWA

```
http://localhost:5000
```

Ви побачите **реальне відео з камери** та детекцію об'єктів!

---

## 📹 Варіанти Джерел Камери

### Опція 1: Камера Ноутбука (Webcam)

**Найпростіший спосіб!**

```yaml
development:
  camera_source: "webcam"
```

```powershell
# Тест камери
python scripts/test_camera_modes.py --source webcam
```

### Опція 2: Камера Смартфона (IP Camera)

**Кроки:**

1. Встановіть на телефон **IP Webcam** (Android) або **EpocCam** (iOS)
2. Запустіть додаток та знайдіть IP-адресу (наприклад, `http://192.168.1.100:8080/video`)
3. Налаштуйте в `config.yaml`:

```yaml
development:
  camera_source: "ip_camera"
  ip_camera_url: "http://192.168.1.100:8080/video"
```

4. Запустіть:

```powershell
python scripts/test_camera_modes.py --source ip_camera --ip-camera-url "http://192.168.1.100:8080/video"
```

**Переваги:**
- ✅ Краща якість камери
- ✅ Можна виносити телефон на вулицю
- ✅ Реальна якість як на роботі

### Опція 3: Відеофайл

**Для тестування на записаному відео:**

1. Покладіть відео в `data/test_video.mp4`
2. Налаштуйте:

```yaml
development:
  camera_source: "video_file"
  video_file_path: "data/test_video.mp4"
```

3. Запустіть:

```powershell
python scripts/test_camera_modes.py --source video_file --video-file "data/test_video.mp4"
```

### Опція 4: Папка з Зображеннями

**Для тестування на фото:**

1. Покладіть фото в `data/test_images/`
2. Налаштуйте:

```yaml
development:
  camera_source: "images"
  images_folder: "data/test_images"
```

3. Запустіть:

```powershell
python scripts/test_camera_modes.py --source images --images-folder "data/test_images"
```

---

## 🧪 Тестування Детекції

### Простий Тест Камери

```powershell
# Тільки відео без детекції
python scripts/test_camera_modes.py --source webcam
```

**Клавіші:**
- `q` - вийти
- `s` - зберегти кадр у `data/captures/`

### Тест з YOLO Детекцією

```powershell
# З детекцією об'єктів
python scripts/test_camera_modes.py --source webcam --with-detection
```

Ви побачите:
- ✅ Bounding boxes навколо об'єктів
- ✅ Labels з класами та confidence
- ✅ FPS в реальному часі

---

## 🗺️ Симуляція GPS

Система генерує **реалістичні GPS дані**:

- 📍 Стартова точка: Київ (50.4501°N, 30.5234°E)
- 🔄 Рух по колу радіусом ~11 метрів
- 📊 RTK Fixed якість (найкраща)
- 🛰️ 12 супутників

**Дані оновлюються в реальному часі:**

```python
# В логах ви побачите
🔧 Mock GPS: Lat=50.4501, Lon=30.5235, Speed=0.52 m/s, Heading=45.2°
```

---

## 🚗 Симуляція Моторів

Команди моторам виводяться в лог:

```python
🔧 Mock motors: L=0.50, R=0.50  # Вперед
🔧 Mock motors: L=0.30, R=0.70  # Поворот праворуч
🔧 Mock motors: L=0.00, R=0.00  # Стоп
```

**Тестування керування:**

1. Відкрийте PWA: `http://localhost:5000`
2. Перейдіть в розділ "Control"
3. Натисніть START/PAUSE/STOP
4. Дивіться логи в консолі

---

## 🌿 Симуляція Weeder

Відстеження активацій механізму:

```python
🔧 Mock weeder activated #1 at position (10.5, 20.3)
🔧 Mock weeding complete (total: 1)
```

**Перевірка історії:**

```python
from src.weeding.weeder import MockWeeder

weeder = MockWeeder()
weeder.setup()

# Після роботи
stats = weeder.get_statistics()
print(f"Total activations: {stats['total_actions']}")
```

---

## 📊 Повна Система на ПК

### Запуск Повної Системи

```powershell
# 1. Встановіть залежності
pip install opencv-python numpy ultralytics Flask Flask-SocketIO paho-mqtt PyYAML

# 2. Налаштуйте config.yaml
development:
  enabled: true
  camera_source: "webcam"

# 3. Запустіть
python main.py
```

### Що Працює:

✅ **Backend**
- Flask API на `http://localhost:5000/api`
- SocketIO для real-time оновлень
- MQTT телеметрія (якщо mosquitto встановлено)

✅ **Vision**
- Камера ноутбука/телефону
- YOLOv8 детекція
- Preprocessing та enhancement

✅ **Navigation**
- Симуляція GPS з реалістичним рухом
- Kalman Filter для згладжування
- Віртуальна траєкторія

✅ **Control**
- Симуляція моторів
- PID контролер
- Pure Pursuit алгоритм

✅ **Frontend (PWA)**
- Dashboard з live відео
- Карта з GPS позицією
- Панель керування
- Статистика детекцій

---

## 🐛 Troubleshooting

### Проблема: Камера не відкривається

```python
# Спробуйте різні індекси
python scripts/test_camera_modes.py --source webcam --webcam-index 0
python scripts/test_camera_modes.py --source webcam --webcam-index 1
```

### Проблема: IP-камера не підключається

1. Перевірте, що телефон та ПК в одній WiFi мережі
2. Перевірте URL (має бути щось як `http://192.168.1.100:8080/video`)
3. Спробуйте відкрити URL у браузері

### Проблема: Низький FPS

```yaml
# Зменшіть роздільність
camera:
  resolution: [640, 480]  # Замість [1920, 1080]
  framerate: 15           # Замість 30
```

### Проблема: YOLO не завантажується

```powershell
# Встановіть правильну версію
pip install ultralytics torch torchvision

# Використовуйте .pt замість .tflite для тестування
detection:
  model_path: "models/yolov8n.pt"
```

---

## 📱 Інструкція: IP Webcam на Android

### Крок 1: Встановлення

1. Відкрийте Google Play
2. Знайдіть "IP Webcam"
3. Встановіть від Pavel Khlebovich

### Крок 2: Налаштування

1. Запустіть додаток
2. Прокрутіть вниз до "Start server"
3. Натисніть кнопку

### Крок 3: Отримання URL

На екрані з'явиться:
```
http://192.168.1.XXX:8080
```

Додайте `/video` в кінець:
```
http://192.168.1.XXX:8080/video
```

### Крок 4: Налаштування в Проекті

```yaml
development:
  camera_source: "ip_camera"
  ip_camera_url: "http://192.168.1.XXX:8080/video"
```

### Крок 5: Тест

```powershell
python scripts/test_camera_modes.py --source ip_camera --ip-camera-url "http://192.168.1.XXX:8080/video"
```

---

## 🎯 Рекомендації для Захисту Дипломної Роботи

### Демонстрація на Захисті

**Варіант 1: Ноутбук + Webcam**
```powershell
python main.py
# Відкрити http://localhost:5000 на екрані
# Показати live детекцію на webcam
```

**Варіант 2: Ноутбук + Телефон як Камера**
```powershell
# Використати IP Webcam
# Виносити телефон до різних об'єктів
# Показати детекцію в реальному часі
```

**Варіант 3: Підготовлене Відео**
```powershell
# Записати відео з полю/городу
# Запустити на відео
# Показати автоматичну детекцію
```

### Що Показувати Комісії:

1. **PWA Dashboard** - професійний інтерфейс
2. **Live детекція** - YOLOv8 в дії
3. **GPS карта** - віртуальний рух
4. **Панель керування** - Start/Pause/Stop
5. **Статистика** - графіки та метрики
6. **Мобільний додаток** - React Native (опціонально)

---

## 🔄 Перехід на Raspberry Pi

Коли купите Raspberry Pi:

1. Скопіюйте проект на Pi
2. Встановіть залежності: `./scripts/deploy_raspberry_pi.sh`
3. Змініть в `config.yaml`:

```yaml
development:
  enabled: false  # ❌ Вимкнути dev mode
```

4. Запустіть: `python main.py`

**Система автоматично** перемкнеться на:
- PiCamera2 замість webcam
- Реальний GPS (u-blox ZED-F9P)
- Реальні мотори (GPIO PWM)
- Реальний weeder механізм

**Код не треба міняти!** Все працює автоматично.

---

## 📚 Додаткові Матеріали

- [HOW_TO_TEST.md](HOW_TO_TEST.md) - Повна інструкція тестування
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архітектура системи
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Керівництво користувача

---

## 💡 Поради

### Для Розробки

1. Використовуйте webcam для швидкого тестування
2. Тестуйте детекцію на різних об'єктах (книги, кружки, рослини)
3. Перевіряйте PWA в різних браузерах
4. Логи дивіться в `data/logs/robot.log`

### Для Демонстрації

1. Підготуйте відео з реальним полем/городом
2. Протестуйте все заздалегідь
3. Майте резервний варіант (webcam)
4. Покажіть і десктопну, і мобільну версії

### Для Дипломної Роботи

1. Зробіть скріншоти всіх екранів PWA
2. Запишіть відео роботи системи
3. Підготуйте діаграми з ARCHITECTURE.md
4. Покажіть код симуляції як додатковий функціонал

---

## ✅ Чеклист Тестування

- [ ] Webcam працює
- [ ] IP-камера підключається (якщо використовується)
- [ ] YOLO детекція працює
- [ ] PWA відкривається
- [ ] Live відео відображається на dashboard
- [ ] GPS симуляція показує рух на карті
- [ ] Кнопки керування (Start/Pause/Stop) працюють
- [ ] Логи виводяться правильно
- [ ] Можна зберегти кадр (клавіша 's')
- [ ] FPS стабільний (>10 fps)

---

**Готово! Тепер ви можете повноцінно тестувати систему на ПК без Raspberry Pi! 🎉**
