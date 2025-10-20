# 🚀 Швидкий Старт на ПК (БЕЗ Raspberry Pi)

## ✅ Все Вже Встановлено!

Всі необхідні бібліотеки вже встановлені та працюють:
- ✅ OpenCV (камера)
- ✅ NumPy, Pillow (обробка зображень)
- ✅ YOLOv8 / Ultralytics (детекція)
- ✅ Flask, SocketIO (веб-сервер)
- ✅ PyYAML, Loguru (конфігурація та логи)

---

## 🎥 1. Тест Камери (30 секунд)

### Перевірка Webcam

```powershell
python scripts/test_camera_modes.py --source webcam
```

**Що побачите:**
- Вікно з відео з вашої webcam
- FPS в реальному часі
- Лічильник кадрів

**Клавіші:**
- `q` - вийти
- `s` - зберегти кадр

### Якщо у вас кілька камер

```powershell
# Спробуйте різні індекси
python scripts/test_camera_modes.py --source webcam --webcam-index 0
python scripts/test_camera_modes.py --source webcam --webcam-index 1
```

---

## 🤖 2. Тест YOLO Детекції (1 хвилина)

```powershell
python scripts/test_camera_modes.py --source webcam --with-detection
```

**Що побачите:**
- Bounding boxes навколо об'єктів
- Labels з класами (person, cup, book, etc.)
- Confidence scores

**Покажіть камері:**
- Чашку ☕
- Книгу 📖
- Телефон 📱
- Свою руку ✋
- Рослину 🌱

---

## 🌐 3. Запуск Повної Системи (2 хвилини)

### Крок 1: Налаштування

Відкрийте `config/config.yaml` і перевірте:

```yaml
development:
  enabled: true  # ✅ Має бути true
  camera_source: "webcam"
  simulate_gps: true
  simulate_motors: true
  simulate_sensors: true
```

### Крок 2: Запуск

```powershell
python main.py
```

**Що побачите в консолі:**

```
============================================================
Initializing Weed Removal Robot System
============================================================
🔧 DEVELOPMENT MODE: Using webcam
Initializing vision subsystem...
✅ Camera started successfully!
🔧 DEVELOPMENT MODE: Using simulated GPS
🔧 DEVELOPMENT MODE: Using simulated motors
🔧 DEVELOPMENT MODE: Using simulated weeder
All subsystems started successfully
```

### Крок 3: Відкрити PWA

Відкрийте браузер:
```
http://localhost:5000
```

**Що побачите:**
- 🏠 **Dashboard** - live відео з камери
- 🗺️ **Map** - GPS карта з віртуальним рухом
- 🎮 **Control** - кнопки Start/Pause/Stop
- 📊 **Stats** - статистика детекцій

---

## 📱 4. Використання Камери Смартфона (ОПЦІОНАЛЬНО)

### Android: IP Webcam

1. **Встановіть додаток:**
   - Відкрийте Google Play
   - Знайдіть "IP Webcam" (Pavel Khlebovich)
   - Встановіть

2. **Запустіть сервер:**
   - Відкрийте додаток
   - Прокрутіть вниз до "Start server"
   - Натисніть

3. **Скопіюйте URL:**
   ```
   http://192.168.1.XXX:8080/video
   ```

4. **Налаштуйте в config.yaml:**
   ```yaml
   development:
     camera_source: "ip_camera"
     ip_camera_url: "http://192.168.1.XXX:8080/video"
   ```

5. **Тест:**
   ```powershell
   python scripts/test_camera_modes.py --source ip_camera --ip-camera-url "http://192.168.1.XXX:8080/video"
   ```

### iOS: EpocCam

1. Встановіть EpocCam з App Store
2. Встановіть драйвери на ПК з kinoni.com
3. Камера з'явиться як звичайна webcam (індекс 1 або 2)

```powershell
python scripts/test_camera_modes.py --source webcam --webcam-index 1
```

---

## 🐛 Troubleshooting

### Проблема: Камера не відкривається

**Рішення 1:** Перевірте індекс камери
```powershell
# Спробуйте різні індекси
python scripts/test_camera_modes.py --source webcam --webcam-index 0
python scripts/test_camera_modes.py --source webcam --webcam-index 1
python scripts/test_camera_modes.py --source webcam --webcam-index 2
```

**Рішення 2:** Закрийте інші програми, які використовують камеру (Zoom, Skype, Teams)

**Рішення 3:** Перезавантажте ПК

### Проблема: Низький FPS

**Рішення:** Зменшіть роздільність в `config.yaml`
```yaml
camera:
  resolution: [640, 480]  # Замість [1920, 1080]
```

### Проблема: YOLO модель не завантажується

**Рішення:** Використовуйте онлайн модель
```yaml
detection:
  model_path: "yolov8n.pt"  # Автоматично завантажиться
```

### Проблема: IP-камера не підключається

**Чеклист:**
- [ ] Телефон та ПК в одній WiFi мережі
- [ ] URL правильний (`/video` в кінці)
- [ ] Firewall не блокує з'єднання
- [ ] URL відкривається в браузері

---

## 📊 Що Працює в Режимі Розробки

### ✅ Повністю Працює:

- **Камера:** Webcam, IP-камера, відео файли
- **YOLO Детекція:** Всі класи (80+ об'єктів)
- **Веб-інтерфейс:** PWA з live відео
- **API:** REST endpoints та SocketIO
- **Логування:** Всі події в консолі та файлах

### 🔧 Симулюється:

- **GPS:** Віртуальний рух по Києву
- **Мотори:** Команди виводяться в лог
- **Weeder:** Рахується кількість активацій
- **GPIO:** Mock класи замість справжніх

### ❌ Не Працює (Потрібен Raspberry Pi):

- Реальний RTK GPS (u-blox ZED-F9P)
- PWM мотори через GPIO
- Механізм прополювання
- IMU сенсор

---

## 🎯 Для Захисту Дипломної Роботи

### Рекомендована Демонстрація:

1. **Показати живу детекцію:**
   ```powershell
   python scripts/test_camera_modes.py --source webcam --with-detection
   ```
   - Покажіть різні об'єкти камері
   - Поясніть як працює YOLO

2. **Запустити повну систему:**
   ```powershell
   python main.py
   ```
   - Відкрийте PWA: http://localhost:5000
   - Покажіть всі екрани (Dashboard, Map, Control, Stats)

3. **Показати мобільний додаток:**
   - Відкрийте PWA на телефоні
   - Покажіть offline режим
   - Згадайте про React Native версію

4. **Пояснити архітектуру:**
   - Покажіть `docs/ARCHITECTURE.md`
   - Поясніть модульну структуру
   - Розкажіть про режим розробки

### Що Підкреслити:

- ✅ **Гнучкість:** Працює і на ПК, і на Raspberry Pi
- ✅ **Сучасні технології:** YOLOv8, PWA, React Native, SocketIO
- ✅ **Тестованість:** Можна тестувати без апаратури
- ✅ **Документація:** 2500+ рядків документації
- ✅ **Продакшн готовність:** SystemD service, deployment scripts

---

## 📚 Додаткові Матеріали

- 📖 [DEVELOPMENT_MODE.md](docs/DEVELOPMENT_MODE.md) - Детальний гайд
- 📖 [HOW_TO_TEST.md](docs/HOW_TO_TEST.md) - Інструкції тестування
- 📖 [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архітектура системи
- 📖 [README.md](README.md) - Головна документація

---

## ✅ Чеклист Перед Захистом

- [ ] Webcam тест працює
- [ ] YOLO детекція працює
- [ ] PWA відкривається на localhost:5000
- [ ] Live відео відображається на dashboard
- [ ] GPS симуляція показує рух на карті
- [ ] Кнопки Start/Pause/Stop реагують
- [ ] Мобільна версія PWA працює на телефоні
- [ ] Всі логи виводяться правильно
- [ ] Скріншоти всіх екранів готові
- [ ] Презентація підготовлена

---

## 🎉 Готово!

**Тепер ви можете:**
- ✅ Тестувати систему на ПК
- ✅ Показати роботу на захисті
- ✅ Розробляти без Raspberry Pi
- ✅ Перевірити всі функції

**Після купівлі Raspberry Pi:**
- Просто змініть `development.enabled: false` в config.yaml
- Система автоматично перемкнеться на реальне залізо
- Код міняти НЕ треба!

---

**Успіхів на захисті! 🎓🚀**
