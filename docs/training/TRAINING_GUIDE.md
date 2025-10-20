# Посібник з тренування моделі детекції бур'янів

## Огляд

Цей посібник описує процес тренування YOLOv8 моделі для детекції бур'янів.

## Датасети для детекції бур'янів

### 1. DeepWeeds Dataset

**Опис**: Найбільший публічний датасет для детекції бур'янів
**Розмір**: 17,509 зображень
**Класи**: 8 видів бур'янів + фон
**Країна**: Австралія
**Роздільність**: 256×256 пікселів

**Класи бур'янів**:
- Chinee apple (Китайське яблуко)
- Lantana (Лантана)
- Parkinsonia (Паркінсонія)
- Parthenium (Партеніум)
- Prickly acacia (Колюча акація)
- Rubber vine (Гумова лоза)
- Siam weed (Сіамський бур'ян)
- Snake weed (Зміїний бур'ян)
- Negative (Фон - без бур'янів)

**Завантаження**:
```bash
python scripts/download_dataset.py deepweeds
```

### 2. Crop/Weed Field Image Dataset (CWFID)

**Опис**: Реальні польові зображення з анотаціями
**Класи**: crop (культура), weed (бур'ян)
**GitHub**: https://github.com/cwfid/dataset

### 3. Roboflow Datasets

**Опис**: Готові датасети з Roboflow Universe
**Формат**: YOLOv8-ready
**Завантаження**:
```bash
# Потрібен API ключ з roboflow.com
python scripts/download_dataset.py roboflow-agriculture --api-key YOUR_KEY
```

### 4. Власний датасет

Створення власного датасету:
```bash
python scripts/download_dataset.py sample
```

## Підготовка датасету

### Структура даних

```
data/datasets/your_dataset/
├── data.yaml              # Конфігураційний файл
├── train/
│   ├── images/           # Тренувальні зображення
│   └── labels/           # YOLO анотації (.txt)
├── val/
│   ├── images/           # Валідаційні зображення
│   └── labels/           # YOLO анотації (.txt)
└── test/                 # Тестовий набір (опціонально)
    ├── images/
    └── labels/
```

### Формат data.yaml

```yaml
path: /path/to/dataset
train: train/images
val: val/images
test: test/images

nc: 2  # Кількість класів
names: ['weed', 'crop']  # Назви класів
```

### Формат анотацій YOLO

Кожне зображення має відповідний .txt файл з анотаціями:

```
<class_id> <x_center> <y_center> <width> <height>
```

Де:
- `class_id`: індекс класу (починається з 0)
- Всі координати нормалізовані до [0, 1]

Приклад:
```
0 0.5 0.5 0.2 0.3
1 0.3 0.7 0.15 0.25
```

## Тренування моделі

### Базове тренування

```bash
python scripts/train_yolo.py \
    --data data/datasets/deepweeds/data.yaml \
    --model n \
    --epochs 100 \
    --batch 16
```

### Параметри моделі

**Розміри моделей YOLOv8**:

| Модель | Параметри | Розмір | Швидкість | mAP |
|--------|-----------|---------|-----------|-----|
| YOLOv8n | 3.2M | 6.2 MB | Найшвидша | Базова |
| YOLOv8s | 11.2M | 21.5 MB | Швидка | Добра |
| YOLOv8m | 25.9M | 49.7 MB | Середня | Краща |
| YOLOv8l | 43.7M | 83.7 MB | Повільна | Відмінна |
| YOLOv8x | 68.2M | 130.5 MB | Найповільніша | Найкраща |

**Рекомендації**:
- **Raspberry Pi**: YOLOv8n (nano) - оптимальний баланс
- **Jetson Nano**: YOLOv8s (small) - краща точність
- **Потужні системи**: YOLOv8m (medium) - висока точність

### Розширене тренування

```bash
python scripts/train_yolo.py \
    --data data/datasets/deepweeds/data.yaml \
    --model s \
    --epochs 150 \
    --batch 32 \
    --img-size 640 \
    --patience 50 \
    --device 0 \
    --project runs/train \
    --name weed_detection_v1
```

### Параметри тренування

**Основні параметри**:
- `--model`: Розмір моделі (n, s, m, l, x)
- `--epochs`: Кількість епох (100-200)
- `--batch`: Розмір батчу (залежить від GPU пам'яті)
- `--img-size`: Розмір зображення (640, 1280)
- `--patience`: Early stopping (50)
- `--device`: GPU (0, 1, ...) або CPU (cpu)

**Augmentation** (вже налаштовано в скрипті):
- HSV: Зміна кольорів
- Flip: Віддзеркалення
- Translate: Зсув
- Scale: Масштабування
- Mosaic: Мозаїчна аугментація

## Валідація моделі

```bash
python scripts/train_yolo.py \
    --validate \
    --weights runs/train/weed_detection/weights/best.pt \
    --data data/datasets/deepweeds/data.yaml
```

## Експорт моделі

### TensorFlow Lite (для Raspberry Pi)

```bash
# Float32
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format tflite

# INT8 quantization (менший розмір, швидша інференція)
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format tflite \
    --int8
```

### Інші формати

```bash
# ONNX (універсальний формат)
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format onnx

# TensorRT (NVIDIA GPU)
python scripts/train_yolo.py \
    --export \
    --weights runs/train/weed_detection/weights/best.pt \
    --format engine
```

## Використання натренованої моделі

### Оновлення конфігурації

Після тренування оновіть `config/config.yaml`:

```yaml
detection:
  model_path: "models/best.tflite"  # Або best_int8.tflite
  confidence_threshold: 0.5
  iou_threshold: 0.45
```

### Копіювання моделі

```bash
cp runs/train/weed_detection/weights/best.tflite models/
```

### Тестування детекції

```python
from src.detection.yolo_detector import YOLODetector
from src.vision.camera import Camera
from src.vision.preprocessor import ImagePreprocessor

# Ініціалізація
camera = Camera()
preprocessor = ImagePreprocessor()
detector = YOLODetector(
    model_path="models/best.tflite",
    confidence_threshold=0.5
)

# Запуск
camera.start()
detector.load_model()

# Детекція
frame = camera.capture()
processed = preprocessor.preprocess(frame)
detections = detector.detect(processed)

print(f"Detected {len(detections)} objects")
for det in detections:
    print(f"  - {det.class_name}: {det.confidence:.2f}")
```

## Tips для кращої точності

### 1. Збалансований датасет

- Однакова кількість зображень кожного класу
- Різноманітні умови освітлення
- Різні стадії росту бур'янів

### 2. Якісні анотації

- Точні bounding boxes
- Консистентне позначення класів
- Перевірка помилок анотування

### 3. Data Augmentation

- Horizontal flip (для симетричних об'єктів)
- Color jittering (різне освітлення)
- Mosaic (контекст навколишнього середовища)

### 4. Гіперпараметри

Початкові налаштування:
```python
lr0 = 0.01          # Початковий learning rate
lrf = 0.01          # Кінцевий learning rate
momentum = 0.937    # SGD momentum
weight_decay = 0.0005
warmup_epochs = 3   # Warmup період
```

### 5. Мониторинг тренування

Використовуйте TensorBoard:
```bash
tensorboard --logdir runs/train
```

## Troubleshooting

### Out of Memory (OOM)

Зменшіть:
- Batch size: `--batch 8`
- Image size: `--img-size 416`
- Модель: `--model n`

### Низька точність

- Збільшіть кількість епох
- Використайте більшу модель
- Покращіть якість датасету
- Налаштуйте гіперпараметри

### Overfitting

- Збільшіть data augmentation
- Використайте dropout
- Зменшіть розмір моделі
- Збільшіть розмір датасету

## Benchmark результати

Типові показники на Raspberry Pi 4:

| Модель | FPS | mAP50 | Розмір | Інференція |
|--------|-----|-------|--------|------------|
| YOLOv8n | 15-20 | 0.85 | 6 MB | ~50ms |
| YOLOv8n-INT8 | 20-25 | 0.83 | 3 MB | ~40ms |
| YOLOv8s | 8-12 | 0.89 | 22 MB | ~80ms |

## Ресурси

- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/)
- [DeepWeeds Paper](https://www.nature.com/articles/s41598-018-38343-3)
- [Roboflow Universe](https://universe.roboflow.com/)
- [YOLO Format Converter](https://roboflow.com/convert)
