# 📱 Повний посібник з тестування та розгортання

## Архітектура системи

```
┌─────────────────┐          ┌──────────────────┐
│  Raspberry Pi   │◄────────►│  Weed Robot      │
│  (Flask Server) │  Serial  │  (Hardware)      │
│  Port: 5000     │  & GPIO  │                  │
└────────┬────────┘          └──────────────────┘
         │
         │ WiFi Network (192.168.x.x)
         │
         ├──────────────┬──────────────┬─────────────┐
         │              │              │             │
    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐   ┌───▼───┐
    │ Browser │    │ Browser │   │ Android │   │  iOS  │
    │   PWA   │    │ Desktop │   │   App   │   │  PWA  │
    │ (Phone) │    │   PWA   │   │  (RN)   │   │(Phone)│
    └─────────┘    └─────────┘   └─────────┘   └───────┘
```

## 🎯 Частина 1: Налаштування Raspberry Pi

### 1.1 Підготовка Raspberry Pi

```powershell
# На вашому Windows ПК підключіться до Raspberry Pi через SSH
ssh pi@raspberrypi.local
# або використовуйте IP адресу
ssh pi@192.168.1.100
```

### 1.2 Встановлення залежностей

```bash
# Оновіть систему
sudo apt update && sudo apt upgrade -y

# Встановіть системні пакети
sudo apt install -y python3-pip git mosquitto mosquitto-clients

# Клонуйте проект (якщо ще не зроблено)
git clone https://github.com/SASCYT9/weed-removal-system.git
cd weed-removal-system

# Встановіть Python залежності
pip3 install -r requirements.txt

# Встановіть MQTT брокер як сервіс
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 1.3 Налаштування WiFi точки доступу (опціонально)

Якщо хочете, щоб робот створював власну WiFi мережу:

```bash
# Встановіть hostapd та dnsmasq
sudo apt install -y hostapd dnsmasq

# Налаштуйте hostapd
sudo nano /etc/hostapd/hostapd.conf
```

Додайте конфігурацію:
```
interface=wlan0
driver=nl80211
ssid=WeedBot-Robot
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=WeedBot2025
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

### 1.4 Запуск веб-сервера

```bash
# Перевірте конфігурацію
cat config/config.yaml

# Запустіть сервер
python3 main.py

# Або запустіть у фоновому режимі
nohup python3 main.py > robot.log 2>&1 &
```

### 1.5 Автозапуск при завантаженні

```bash
# Створіть systemd сервіс
sudo nano /etc/systemd/system/weedbot.service
```

Додайте:
```ini
[Unit]
Description=WeedBot Robot Control System
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/weed-removal-system
ExecStart=/usr/bin/python3 /home/pi/weed-removal-system/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активуйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable weedbot
sudo systemctl start weedbot
sudo systemctl status weedbot
```

## 🌐 Частина 2: Тестування PWA (Progressive Web App)

### 2.1 Перевірка сервера

```powershell
# На Windows ПК знайдіть IP адресу Raspberry Pi
# На Raspberry Pi виконайте:
hostname -I
# Наприклад: 192.168.1.100
```

### 2.2 Доступ до PWA

**На Android телефоні:**

1. Відкрийте Chrome
2. Введіть адресу: `http://192.168.1.100:5000`
3. Зачекайте завантаження інтерфейсу
4. Натисніть кнопку **"📱 Встановити додаток"** (з'явиться внизу справа)
5. Або: Меню (⋮) → "Add to Home screen"
6. Іконка WeedBot з'явиться на домашньому екрані

**На iPhone/iPad:**

1. Відкрийте Safari
2. Введіть адресу: `http://192.168.1.100:5000`
3. Натисніть кнопку "Share" (квадрат зі стрілкою)
4. Виберіть "Add to Home Screen"
5. Підтвердіть назву та додайте

**На Windows ПК:**

1. Відкрийте Chrome або Edge
2. Введіть адресу: `http://192.168.1.100:5000`
3. В адресному рядку з'явиться іконка установки (комп'ютер з стрілкою)
4. Натисніть "Install WeedBot"
5. Додаток буде доступний як окреме вікно

### 2.3 Тестування функцій PWA

**Онлайн режим:**
- ✅ Статус робота оновлюється в реальному часі
- ✅ GPS координати відображаються
- ✅ Кнопки керування працюють (Start/Pause/Stop/Reset)
- ✅ Статистика оновлюється

**Офлайн режим:**
- ✅ Відключіть WiFi на телефоні
- ✅ Додаток залишається відкритим
- ✅ З'явиться банер "Ви в офлайн режимі"
- ✅ Команди зберігаються та надсилаються при відновленні з'єднання

**Оновлення:**
- ✅ При оновленні коду з'явиться банер "Доступне оновлення!"
- ✅ Натисніть "Оновити зараз" для миттєвого оновлення

## 📱 Частина 3: Збірка та тестування Android додатку (React Native)

### 3.1 Підготовка Windows ПК

**Встановіть необхідне ПЗ:**

```powershell
# 1. Node.js LTS (18.x або новіше)
# Завантажте з https://nodejs.org/

# Перевірте встановлення
node --version  # v18.17.0 або новіше
npm --version   # 9.6.7 або новіше

# 2. Android Studio
# Завантажте з https://developer.android.com/studio
# Під час установки виберіть:
# - Android SDK
# - Android SDK Platform
# - Android Virtual Device
```

**Налаштуйте змінні середовища:**

```powershell
# Додайте в PATH (Системні налаштування → Змінні середовища):
ANDROID_HOME = C:\Users\YourUsername\AppData\Local\Android\Sdk

# Додайте до Path:
%ANDROID_HOME%\platform-tools
%ANDROID_HOME%\tools
%ANDROID_HOME%\emulator
```

### 3.2 Ініціалізація React Native проекту

```powershell
# Перейдіть до папки mobile-app
cd "d:\Diplom Code\weed-removal-system\mobile-app"

# Встановіть залежності
npm install

# Для Windows можливо знадобиться:
npm install --legacy-peer-deps
```

### 3.3 Налаштування IP адреси робота

```powershell
# Відредагуйте файл конфігурації
notepad src\utils\constants.ts
```

Змініть IP на вашу Raspberry Pi:
```typescript
export const DEFAULT_SETTINGS = {
  host: '192.168.1.100',  // ← Ваша IP адреса Raspberry Pi
  port: 5000,
  mqttPort: 1883,
};
```

### 3.4 Запуск на емуляторі

```powershell
# Запустіть Metro bundler
npm start

# В новому терміналі запустіть Android
npm run android
```

### 3.5 Запуск на реальному пристрої

**Підготовка телефону:**

1. Увімкніть режим розробника:
   - Налаштування → Про телефон
   - Натискайте "Номер збірки" 7 разів
2. Увімкніть USB налагодження:
   - Налаштування → Для розробників → USB налагодження
3. Підключіть телефон до ПК через USB

**Перевірка підключення:**

```powershell
# Перевірте, чи видно пристрій
adb devices
# Має показати ваш телефон
```

**Запуск додатку:**

```powershell
npm run android
```

### 3.6 Збірка release APK

```powershell
cd android

# Windows
.\gradlew assembleRelease

# APK буде в:
# android\app\build\outputs\apk\release\app-release.apk

# Встановіть на телефон
adb install app\build\outputs\apk\release\app-release.apk
```

## 🧪 Частина 4: Тестування інтеграції з роботом

### 4.1 Перевірка MQTT

```bash
# На Raspberry Pi підпишіться на всі топіки
mosquitto_sub -h localhost -t "weed_robot/#" -v

# В іншому терміналі надішліть тестову команду
mosquitto_pub -h localhost -t "weed_robot/command" -m "start"
```

### 4.2 Перевірка REST API

```powershell
# З Windows ПК
curl http://192.168.1.100:5000/api/status

# Надішліть команду
curl -X POST http://192.168.1.100:5000/api/command `
  -H "Content-Type: application/json" `
  -d '{\"command\": \"start\"}'
```

### 4.3 Тестовий сценарій повної системи

**Крок 1: Запустіть робота**
```bash
# На Raspberry Pi
python3 main.py
```

**Крок 2: Відкрийте PWA на телефоні**
```
http://192.168.1.100:5000
```

**Крок 3: Перевірте функції:**

✅ Натисніть "▶️ Старт"
  - Статус має змінитися на "Running"
  - В логах Raspberry Pi має з'явитися "Received command: start"

✅ Перевірте GPS (якщо підключений GPS модуль)
  - GPS Fix має показувати статус
  - Координати мають оновлюватися

✅ Тест детекції (якщо є камера)
  - Направте камеру на об'єкт
  - В розділі "Детекції" мають з'явитися результати

✅ Натисніть "⏹️ Стоп"
  - Статус має змінитися на "Idle"

**Крок 4: Тест офлайн режиму**

1. Увімкніть авіарежим на телефоні
2. PWA має продовжувати працювати
3. Натисніть команди - вони збережуться
4. Вимкніть авіарежим
5. Команди автоматично надішляться

## 📊 Частина 5: Моніторинг та налагодження

### 5.1 Перегляд логів

```bash
# На Raspberry Pi
# Лог веб-сервера
tail -f robot.log

# Лог systemd сервісу
sudo journalctl -u weedbot -f

# Лог MQTT
sudo tail -f /var/log/mosquitto/mosquitto.log
```

### 5.2 Налагодження проблем

**Проблема: PWA не встановлюється**
```bash
# Перевірте HTTPS або localhost
# PWA працює тільки на:
# - https://...
# - http://localhost
# - http://192.168.x.x (локальна мережа)

# Перевірте manifest.json
curl http://192.168.1.100:5000/static/manifest.json
```

**Проблема: Не підключається до Raspberry Pi**
```powershell
# Перевірте з'єднання
ping 192.168.1.100

# Перевірте, чи запущений сервер
curl http://192.168.1.100:5000
```

**Проблема: Android додаток не збирається**
```powershell
# Очистіть кеш
cd mobile-app
rm -rf node_modules
npm install

cd android
.\gradlew clean
cd ..
npm run android
```

## 🎓 Частина 6: Демонстрація для дипломної роботи

### 6.1 Підготовка презентації

**Що показати:**

1. ✅ **Архітектура системи** - діаграма компонентів
2. ✅ **Веб-інтерфейс** - PWA на різних пристроях
3. ✅ **Мобільний додаток** - Android версія
4. ✅ **Реальний робот** - запуск та керування
5. ✅ **Детекція** - розпізнавання бур'янів в реальному часі
6. ✅ **GPS навігація** - RTK позиціонування
7. ✅ **Офлайн режим** - робота без інтернету
8. ✅ **Статистика** - аналітика роботи

### 6.2 Сценарій демонстрації (5 хвилин)

**00:00-00:30** - Запуск системи
- Показати Raspberry Pi з роботом
- Продемонструвати запуск сервера

**00:30-01:30** - PWA на телефоні
- Відкрити інтерфейс
- Показати установку як додаток
- Демо керування

**01:30-02:30** - Автономна робота
- Запустити робота
- Показати детекцію бур'янів
- GPS координати в реальному часі

**02:30-03:30** - Мобільний додаток
- Відкрити Android app
- Синхронізація з роботом
- Мапа з позицією

**03:30-04:30** - Офлайн можливості
- Відключити WiFi
- Продемонструвати роботу офлайн
- Синхронізацію при відновленні

**04:30-05:00** - Статистика
- Показати аналітику
- Графіки продуктивності
- Кількість видалених бур'янів

## 📝 Чеклист перед захистом

- [ ] ✅ Raspberry Pi налаштований та працює
- [ ] ✅ Flask сервер запускається автоматично
- [ ] ✅ MQTT брокер активний
- [ ] ✅ PWA встановлений на телефоні
- [ ] ✅ Android додаток зібраний
- [ ] ✅ GPS модуль підключений та працює
- [ ] ✅ Камера захоплює зображення
- [ ] ✅ YOLO модель завантажена
- [ ] ✅ Двигуни реагують на команди
- [ ] ✅ Веддер механізм тестований
- [ ] ✅ Батарея заряджена
- [ ] ✅ Презентація підготовлена
- [ ] ✅ Резервна копія коду зроблена

## 🎉 Успіхів на захисті!

---

**Додаткові ресурси:**

- Документація: `docs/ARCHITECTURE.md`
- Гайд по тренуванню: `docs/training/TRAINING_GUIDE.md`
- Огляд інструментів: `docs/TOOLS_OVERVIEW.md`
- Мобільні додатки: `docs/MOBILE_APPS.md`
