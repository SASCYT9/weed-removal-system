# Повний посібник з використання системи

## Зміст

1. [Підготовка датасету](#1-підготовка-датасету)
2. [Тренування моделі](#2-тренування-моделі)
3. [Калібрування камери](#3-калібрування-камери)
4. [Тестування GPS](#4-тестування-gps)
5. [Планування траєкторій](#5-планування-траєкторій)
6. [Збір тренувальних даних](#6-збір-тренувальних-даних)
7. [Запуск системи](#7-запуск-системи)

---

## 1. Підготовка датасету

### Завантаження публічного датасету

#### DeepWeeds Dataset (рекомендовано)

```bash
# Завантажити DeepWeeds dataset (1.4 GB)
python scripts/download_dataset.py deepweeds

# Датасет буде збережено в: data/datasets/deepweeds/
```

#### Roboflow Dataset

```bash
# Отримайте API ключ на roboflow.com
python scripts/download_dataset.py roboflow-agriculture --api-key YOUR_API_KEY
```

### Створення власного датасету

```bash
# Створити структуру для власного датасету
python scripts/download_dataset.py sample

# Додайте зображення та анотації в:
# - data/datasets/sample/train/images/
# - data/datasets/sample/train/labels/
# - data/datasets/sample/val/images/
# - data/datasets/sample/val/labels/
```

---

## 2. Тренування моделі

### Базове тренування

```bash
# Тренування YOLOv8n (nano) - оптимально для Raspberry Pi
python scripts/train_yolo.py \
    --data data/datasets/deepweeds/data.yaml \
    --model n \
    --epochs 100 \
    --batch 16
```

### Розширене тренування

```bash
# Тренування YOLOv8s з кращою точністю
python scripts/train_yolo.py \
    --data data/datasets/deepweeds/data.yaml \
    --model s \
    --epochs 150 \
    --batch 32 \
    --patience 50 \
    --device 0  # GPU
```

### Валідація моделі

```bash
python scripts/train_yolo.py \
    --validate \
    --weights runs/train/weed_detection/weights/best.pt \
    --data data/datasets/deepweeds/data.yaml
```

### Експорт для Raspberry Pi

```bash
# Float32 TFLite
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format tflite

# INT8 quantized (швидший, менший розмір)
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format tflite \
    --int8

# Копіювання моделі в потрібну директорію
cp runs/train/weed_detection/weights/best.tflite models/
```

---

## 3. Калібрування камери

### Повне калібрування (automated)

```bash
# Автоматичний процес калібрування
python scripts/calibrate_camera.py full --num-images 20

# Інструкції:
# 1. Роздрукуйте шахівницю 9x6 (inner corners)
# 2. Показуйте шахівницю камері з різних кутів
# 3. Натискайте 's' коли кути розпізнані
# 4. Зберіть 20 зображень
```

### Покрокове калібрування

```bash
# Крок 1: Захоплення зображень
python scripts/calibrate_camera.py capture \
    --num-images 20 \
    --output-dir data/calibration

# Крок 2: Розрахунок калібрування
python scripts/calibrate_camera.py calibrate \
    --image-dir data/calibration \
    --output config/camera_calibration.json

# Крок 3: Тестування
python scripts/calibrate_camera.py test \
    --calibration config/camera_calibration.json
```

---

## 4. Тестування GPS

### Тест підключення

```bash
# Базовий тест GPS (10 секунд)
python scripts/test_gps.py test --duration 10

# Перевірка:
# - Чи отримуються дані
# - Частота оновлення
# - Кількість супутників
```

### Моніторинг RTK

```bash
# Моніторинг RTK fix (60 секунд)
python scripts/test_gps.py monitor --duration 60

# Показує:
# - RTK Fixed/Float статус
# - Кількість супутників
# - % RTK fixed
```

### Логування позицій

```bash
# Запис GPS даних (5 хвилин)
python scripts/test_gps.py log \
    --duration 300 \
    --output data/gps_log.csv
```

### Аналіз точності

```bash
# Аналіз точності GPS
python scripts/test_gps.py analyze \
    --log-file data/gps_log.csv

# Показує:
# - Середню позицію
# - Стандартне відхилення (точність)
# - 2D RMS error
# - Розподіл якості fix
```

---

## 5. Планування траєкторій

### Прямокутне поле

```bash
# Boustrophedon pattern (зигзаг)
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern boustrophedon \
    --robot-width 0.5

# Збереження траєкторії
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern boustrophedon \
    --output data/field_path.json \
    --save-plot data/field_path.png
```

### Спіральний паттерн

```bash
# Спіраль всередину
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern spiral \
    --spiral-direction inward
```

### Поворот паттерну

```bash
# Поворот на 45 градусів
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern boustrophedon \
    --angle 45
```

### Нестандартне поле

```bash
# Polygon field
python scripts/plan_field_coverage.py \
    --polygon "0,0 50,0 45,80 5,100" \
    --pattern boustrophedon
```

### Оптимізація

```bash
# З оптимізацією та згладжуванням поворотів
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern boustrophedon \
    --optimize \
    --smooth-turns \
    --turn-radius 1.5
```

---

## 6. Збір тренувальних даних

### Ручний збір з мітками

```bash
# Інтерактивний режим
python scripts/collect_training_data.py manual \
    --output-dir data/my_dataset

# Керування:
# - 's' - зберегти зображення
# - 'w' - зберегти з міткою "weed"
# - 'c' - зберегти з міткою "crop"
# - 'q' - вийти
```

### Автоматичний збір

```bash
# Збір 1 зображення за секунду протягом 5 хвилин
python scripts/collect_training_data.py continuous \
    --interval 1 \
    --duration 300 \
    --output-dir data/my_dataset

# Збір 100 зображень
python scripts/collect_training_data.py continuous \
    --count 100 \
    --output-dir data/my_dataset
```

### Без GPS

```bash
python scripts/collect_training_data.py continuous \
    --no-gps \
    --count 50
```

### Звіт про датасет

```bash
python scripts/collect_training_data.py summary \
    --output-dir data/my_dataset

# Показує:
# - Загальна кількість зображень
# - Розподіл міток
# - Кількість з GPS даними
```

---

## 7. Запуск системи

### Підготовка

1. **Оновіть конфігурацію**:

```bash
nano config/config.yaml
```

Встановіть шлях до моделі:
```yaml
detection:
  model_path: "models/best.tflite"
```

2. **Завантажте траєкторію**:

```python
from src.control.pure_pursuit import PurePursuit
from src.planning.field_coverage import FieldCoveragePlanner

planner = FieldCoveragePlanner()
waypoints = planner.load_path('data/field_path.json')

# В main.py додайте:
robot.pure_pursuit.set_path(waypoints)
```

### Запуск

```bash
# Активувати віртуальне середовище
source venv/bin/activate

# Запуск робота
python main.py

# Або з власною конфігурацією
python main.py --config config/my_config.yaml
```

### Веб-інтерфейс

Відкрийте браузер:
```
http://<raspberry-pi-ip>:5000
```

Функції:
- Перегляд статусу в реальному часі
- GPS позиція та якість
- Детекції бур'янів
- Керування (старт/пауза/стоп)
- Статистика роботи

### MQTT моніторинг

```bash
# Підписка на всі топіки
mosquitto_sub -h localhost -t "weed_robot/#" -v

# Окремі топіки:
mosquitto_sub -h localhost -t "weed_robot/status"
mosquitto_sub -h localhost -t "weed_robot/gps"
mosquitto_sub -h localhost -t "weed_robot/detections"
```

---

## Типовий робочий процес

### Початкове налаштування (один раз)

```bash
# 1. Калібрування камери
python scripts/calibrate_camera.py full

# 2. Тестування GPS
python scripts/test_gps.py test --duration 30
python scripts/test_gps.py monitor --duration 120

# 3. Завантаження датасету
python scripts/download_dataset.py deepweeds

# 4. Тренування моделі
python scripts/train_yolo.py \
    --data data/datasets/deepweeds/data.yaml \
    --model n \
    --epochs 100

# 5. Експорт моделі
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format tflite \
    --int8

# 6. Копіювання моделі
cp runs/train/weed_detection/weights/best_int8.tflite models/best.tflite
```

### Перед кожним сеансом

```bash
# 1. Планування траєкторії
python scripts/plan_field_coverage.py \
    --width 50 \
    --length 100 \
    --pattern boustrophedon \
    --optimize \
    --smooth-turns \
    --output data/today_path.json

# 2. Перевірка GPS
python scripts/test_gps.py test --duration 10

# 3. Запуск системи
python main.py
```

### Збір власних даних

```bash
# 1. Збір зображень у полі
python scripts/collect_training_data.py manual

# 2. Анотування (використайте LabelImg або Roboflow)
# https://github.com/heartexlabs/labelImg

# 3. Тренування на власних даних
python scripts/train_yolo.py \
    --data data/my_dataset/data.yaml \
    --model n \
    --epochs 100

# 4. Валідація
python scripts/train_yolo.py \
    --validate \
    --weights runs/train/my_model/weights/best.pt

# 5. Експорт та використання
python scripts/train_yolo.py \
    --export \
    --weights runs/train/my_model/weights/best.pt \
    --format tflite
```

---

## Troubleshooting

### Камера не працює

```bash
# Перевірка
vcgencmd get_camera
ls /dev/video*

# Налаштування
sudo raspi-config
# Interface Options -> Camera -> Enable
```

### GPS не підключається

```bash
# Перевірка порту
ls -l /dev/ttyACM*
ls -l /dev/ttyUSB*

# Права доступу
sudo usermod -a -G dialout $USER
sudo reboot
```

### YOLO тренування повільне

```bash
# Зменшити розмір батчу
--batch 8

# Використати меншу модель
--model n

# Зменшити розмір зображення
--img-size 416
```

### Out of Memory

```bash
# Raspberry Pi
--model n --batch 4 --img-size 416

# Jetson Nano
--model s --batch 8 --img-size 640
```

---

## Корисні посилання

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [DeepWeeds Paper](https://www.nature.com/articles/s41598-018-38343-3)
- [Roboflow Universe](https://universe.roboflow.com/)
- [LabelImg Tool](https://github.com/heartexlabs/labelImg)
- [RTK GPS Guide](https://learn.sparkfun.com/tutorials/what-is-gps-rtk)

---

## Підтримка

Якщо виникли питання або проблеми:

1. Перевірте логи: `data/logs/robot.log`
2. Переглянт документацію: `docs/`
3. Створіть Issue на GitHub
