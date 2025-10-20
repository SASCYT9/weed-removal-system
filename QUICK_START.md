# WeedBot - Quick Start Guide

## 🚀 Швидкий старт за 5 хвилин

### На Raspberry Pi

```bash
# 1. Клонуйте репозиторій
git clone https://github.com/SASCYT9/weed-removal-system.git
cd weed-removal-system

# 2. Запустіть скрипт розгортання
chmod +x scripts/deploy_raspberry_pi.sh
./scripts/deploy_raspberry_pi.sh

# 3. Запустіть робота
python3 main.py
```

### На телефоні/комп'ютері

```
1. Підключіться до тієї самої WiFi мережі, що і Raspberry Pi
2. Відкрийте браузер
3. Введіть: http://192.168.1.100:5000 (замініть на вашу IP)
4. Натисніть "Встановити додаток"
5. Готово! 🎉
```

## 📱 Як знайти IP адресу Raspberry Pi

```bash
# На Raspberry Pi виконайте:
hostname -I

# Або на Windows:
ping raspberrypi.local
```

## 🎮 Тестування функцій

### 1. Тест веб-інтерфейсу
- Відкрийте браузер: `http://<raspberry-pi-ip>:5000`
- Перевірте, чи відображається статус
- Натисніть кнопки Start/Stop

### 2. Тест MQTT
```bash
# Підпишіться на топіки
mosquitto_sub -h localhost -t "weed_robot/#" -v

# Надішліть команду
mosquitto_pub -h localhost -t "weed_robot/command" -m "start"
```

### 3. Тест GPS (якщо підключений)
```bash
python3 scripts/test_gps.py monitor --duration 60
```

### 4. Тест камери
```bash
python3 scripts/calibrate_camera.py test
```

## 🐛 Розв'язання проблем

### Не можу підключитися до веб-інтерфейсу

```bash
# Перевірте, чи запущений сервер
ps aux | grep python3

# Перевірте порт
netstat -tulpn | grep 5000

# Перезапустіть сервер
pkill -f main.py
python3 main.py
```

### GPS не працює

```bash
# Перевірте підключення
ls -l /dev/serial*
ls -l /dev/ttyACM*

# Тестуйте GPS
python3 scripts/test_gps.py test
```

### Камера не захоплює зображення

```bash
# Перевірте камеру
libcamera-hello --list-cameras

# Тестовий знімок
libcamera-still -o test.jpg
```

## 📞 Потрібна допомога?

Перегляньте повну документацію:
- `docs/TESTING_DEPLOYMENT_GUIDE.md` - Повний гайд
- `docs/ARCHITECTURE.md` - Архітектура системи
- `docs/USAGE_GUIDE.md` - Посібник користувача

---

**Успішної роботи! 🌱🤖**
