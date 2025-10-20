# 🎮 Приклади Використання

## 1️⃣ Швидкий Тест Webcam (10 секунд)

```powershell
python scripts/test_camera_modes.py --source webcam
```

Натисни `q` щоб вийти, `s` щоб зберегти кадр.

---

## 2️⃣ Тест з Детекцією YOLO (30 секунд)

```powershell
python scripts/test_camera_modes.py --source webcam --with-detection
```

Покажи камері:
- ☕ Чашку
- 📱 Телефон
- 📖 Книгу
- ✋ Свою руку

---

## 3️⃣ Повна Система з PWA (1 хвилина)

```powershell
# Запусти систему
python main.py
```

Потім відкрий браузер:
```
http://localhost:5000
```

---

## 4️⃣ Камера Смартфона (Android)

### Крок 1: Встанови IP Webcam
- Google Play → "IP Webcam"
- Запусти → "Start server"

### Крок 2: Скопіюй URL
```
http://192.168.1.XXX:8080/video
```

### Крок 3: Тест
```powershell
python scripts/test_camera_modes.py --source ip_camera --ip-camera-url "http://192.168.1.XXX:8080/video"
```

---

## 5️⃣ Налаштування для Твого ПК

Відкрий `config/config.yaml`:

```yaml
development:
  enabled: true  # ✅ Увімкнути dev mode
  camera_source: "webcam"  # або "ip_camera", "video_file", "images"
  
  # Для IP-камери:
  ip_camera_url: "http://192.168.1.100:8080/video"
  
  # Для відео:
  video_file_path: "data/test_video.mp4"
  
  # Для фото:
  images_folder: "data/test_images"
  
  # Симуляція:
  simulate_gps: true
  simulate_motors: true
  simulate_sensors: true

camera:
  resolution: [1280, 720]  # Зменш якщо лагає
  framerate: 30
  webcam_index: 0  # Спробуй 1, 2 якщо не працює
```

---

## 🐛 Якщо Щось Не Працює

### Камера не відкривається?

```powershell
# Спробуй різні індекси
python scripts/test_camera_modes.py --source webcam --webcam-index 0
python scripts/test_camera_modes.py --source webcam --webcam-index 1
```

### Низький FPS?

Зменш роздільність в `config.yaml`:
```yaml
camera:
  resolution: [640, 480]
```

### YOLO не завантажується?

Використай онлайн модель:
```yaml
detection:
  model_path: "yolov8n.pt"  # Автоматично завантажиться
```

---

## 📱 PWA на Телефоні

1. Відкрий http://[твій-пк-ip]:5000 на телефоні
2. Chrome: "Додати на головний екран"
3. Safari: Поділитися → "На екран Home"

Дізнайся IP ПК:
```powershell
ipconfig  # Шукай IPv4 Address
```

---

## ✅ Перевірка Роботи

```powershell
# 1. Тест камери
python scripts/test_camera_modes.py --source webcam

# 2. Тест детекції
python scripts/test_camera_modes.py --source webcam --with-detection

# 3. Повна система
python main.py
# Відкрий http://localhost:5000

# 4. Перевір логи
# Дивись консоль або data/logs/robot.log
```

---

## 🎯 Для Демонстрації

### Варіант А: Тільки Детекція
```powershell
python scripts/test_camera_modes.py --source webcam --with-detection
```
Показуй різні об'єкти камері в реальному часі.

### Варіант Б: Повна Система
```powershell
python main.py
```
Відкрий PWA та покажи всі екрани.

### Варіант В: Мобільна Демо
1. Запусти систему на ПК
2. Відкрий PWA на телефоні
3. Покажи роботу з телефону

---

**Детальні інструкції:** [QUICK_START_PC.md](QUICK_START_PC.md)

**Troubleshooting:** [DEVELOPMENT_MODE.md](docs/DEVELOPMENT_MODE.md)
