#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌾 ПРОФЕСІЙНА СИСТЕМА ДЕТЕКЦІЇ РОСЛИН v2.0
Повна версія з усіма функціями
"""
import os
import sys
import cv2
import time
import yaml
import threading
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import deque
import numpy as np

# Виправлення кодування для Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Патч для завантаження старих моделей PyTorch
try:
    import torch
    _original_torch_load = torch.load
    def patched_torch_load(f, *args, **kwargs):
        kwargs.setdefault('weights_only', False)
        return _original_torch_load(f, *args, **kwargs)
    torch.load = patched_torch_load
except:
    pass

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit

# === IMPORTS ===
try:
    from ultralytics import YOLO
except ImportError:
    print("❌ ERROR: ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

# Platform detection
IS_RASPBERRY_PI = False
try:
    if os.path.exists('/proc/device-tree/model'):
        IS_RASPBERRY_PI = True
    elif os.path.exists('/proc/cpuinfo'):
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry' in f.read():
                IS_RASPBERRY_PI = True
except:
    pass

if IS_RASPBERRY_PI:
    try:
        from picamera2 import Picamera2
        import psutil
    except ImportError:
        print("⚠️  WARNING: picamera2 or psutil not installed. Will try OpenCV.")
        Picamera2 = None
        # Don't disable IS_RASPBERRY_PI, just fall back to OpenCV later if needed
else:
    Picamera2 = None


# === КОНФІГУРАЦІЯ ===
class Config:
    """Глобальна конфігурація системи"""
    
    def __init__(self):
        self.load_config()
        self.load_plant_classes()
    
    def load_config(self):
        """Завантажити конфігурацію з YAML"""
        config_path = Path('config/config.yaml')
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                    
                self.MODEL_PATH = cfg['model']['path']
                self.MODEL_IMGSZ = cfg['model']['imgsz']
                self.CONFIDENCE_THRESHOLD = cfg['model']['confidence_threshold']
                self.IOU_THRESHOLD = cfg['model']['iou_threshold']
                
                self.CAMERA_TYPE = cfg['camera']['type']
                self.CAMERA_WIDTH = cfg['camera']['width']
                self.CAMERA_HEIGHT = cfg['camera']['height']
                self.CAMERA_FPS = cfg['camera']['fps']
                self.CAMERA_DEVICE = cfg['camera']['device_index']
                
                if IS_RASPBERRY_PI:
                    self.CAMERA_WIDTH = cfg['camera']['pi']['width']
                    self.CAMERA_HEIGHT = cfg['camera']['pi']['height']
                    self.CAMERA_FPS = cfg['camera']['pi']['fps']
                
                self.PROCESS_EVERY_N_FRAMES = cfg['detection']['process_every_n_frames']
                self.MIN_OBJECT_SIZE = cfg['detection']['min_object_size']
                self.ENABLE_TRACKING = cfg['detection']['enable_tracking']
                
                self.WEB_HOST = cfg['web']['host']
                self.WEB_PORT = cfg['web']['port']
                self.JPEG_QUALITY = cfg['web']['jpeg_quality']
                self.STREAM_FPS = cfg['web']['stream_fps']
                
                self.ENABLE_DATABASE = cfg['storage']['enable_database']
                self.DB_PATH = cfg['storage']['db_path']
                self.SAVE_PATH = cfg['storage']['save_path']
            except Exception as e:
                print(f"⚠️  Config load error: {e}, using defaults")
                self.set_defaults()
        else:
            self.set_defaults()
    
    def set_defaults(self):
        """Встановити налаштування за замовчуванням"""
        self.MODEL_PATH = 'best.pt'
        self.MODEL_IMGSZ = 320 if IS_RASPBERRY_PI else 640
        self.CONFIDENCE_THRESHOLD = 0.5
        self.IOU_THRESHOLD = 0.45
        
        self.CAMERA_TYPE = 'auto'
        self.CAMERA_WIDTH = 320 if IS_RASPBERRY_PI else 640
        self.CAMERA_HEIGHT = 240 if IS_RASPBERRY_PI else 480
        self.CAMERA_FPS = 30
        self.CAMERA_DEVICE = 0
        
        self.PROCESS_EVERY_N_FRAMES = 2
        self.MIN_OBJECT_SIZE = 20
        self.ENABLE_TRACKING = True
        
        self.WEB_HOST = '0.0.0.0'
        self.WEB_PORT = 5000
        self.JPEG_QUALITY = 75
        self.STREAM_FPS = 30
        
        self.ENABLE_DATABASE = True
        self.DB_PATH = 'data/detections.db'
        self.SAVE_PATH = 'data/detections/'
    
    def load_plant_classes(self):
        """Завантажити базу даних класів рослин"""
        classes_path = Path('config/plant_classes.yaml')
        if classes_path.exists():
            try:
                with open(classes_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.PLANT_CLASSES = data.get('classes', {})
            except:
                self.PLANT_CLASSES = {}
        else:
            self.PLANT_CLASSES = {}

config = Config()

# === КАМЕРА ===
class UniversalCamera:
    """Універсальний клас для роботи з різними камерами"""
    
    def __init__(self, source='auto', device_id=0):
        self.source = source
        self.device_id = device_id
        self.cap = None
        self.picam = None
        self.running = False
        self.current_source = None
        
    def start(self):
        """Запустити камеру"""
        if self.source == 'auto':
            self.source = 'picamera' if IS_RASPBERRY_PI else 'webcam'
        
        if self.source == 'picamera' and IS_RASPBERRY_PI:
            self._start_picamera()
        elif self.source == 'webcam':
            self._start_webcam()
        elif self.source == 'ip':
            self._start_ip_camera()
        else:
            raise ValueError(f"Unknown camera source: {self.source}")
        
        self.current_source = self.source
        self.running = True
        print(f"✅ Camera: {self.source} ({config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT})")
    
    def _start_picamera(self):
        """Raspberry Pi Camera (Optimized for OV5647)"""
        if Picamera2 is None:
            print("⚠️ Picamera2 library not found, switching to webcam")
            self.source = 'webcam'
            self._start_webcam()
            return

        print("📷 Initializing PiCamera2...")
        self.picam = Picamera2()
        
        # Optimized configuration for OV5647
        controls = {
            "FrameRate": config.CAMERA_FPS,
            "AeEnable": True,
            "AwbEnable": True,
            "Brightness": 0.0,
            "Contrast": 1.0,
            "Saturation": 1.0
        }
        
        # Exposure tuning
        if config.CAMERA_FPS <= 60:
            controls.update({
                "ExposureTime": 12000,
                "AnalogueGain": 2.0
            })

        try:
            # Tight frame duration
            min_us = int(1_000_000 / max(1, config.CAMERA_FPS))
            controls["FrameDurationLimits"] = (min_us, min_us)
        except:
            pass

        camera_config = self.picam.create_preview_configuration(
            main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT), "format": "RGB888"},
            controls=controls
        )
        self.picam.configure(camera_config)
        self.picam.start()
        time.sleep(0.5)
        
        # Post-start tuning
        try:
            if config.CAMERA_FPS <= 60:
                self.picam.set_controls({
                    "AeEnable": True,
                    "AwbEnable": True,
                    "ExposureTime": 15000,
                    "AnalogueGain": 3.0
                })
            else:
                self.picam.set_controls({
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AnalogueGain": 2.5
                })
        except:
            pass
            
        print(f"✅ PiCamera2 started: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}@{config.CAMERA_FPS}fps")
    
    def _start_webcam(self):
        """Веб-камера (OpenCV V4L2)"""
        print(f"📷 Attempting to open webcam (Index: {self.device_id})...")
        
        # Try multiple backends
        backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
        
        for backend in backends:
            self.cap = cv2.VideoCapture(self.device_id, backend)
            if self.cap.isOpened():
                print(f"✅ Camera opened with backend: {backend}")
                break
        
        if not self.cap or not self.cap.isOpened():
            print(f"❌ Failed to open camera index {self.device_id}")
            # Try searching for other indices
            for i in range(10):
                if i == self.device_id: continue
                temp_cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
                if temp_cap.isOpened():
                    print(f"⚠️ Found working camera at index {i}, switching...")
                    self.device_id = i
                    self.cap = temp_cap
                    break
            
            if not self.cap or not self.cap.isOpened():
                raise RuntimeError(f"Could not open any camera")

        # Configure
        # self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        
        # Verify reading
        ret, frame = self.cap.read()
        if not ret:
            print("⚠️ Camera opened but failed to read first frame")
        else:
            print("✅ Camera read test passed")
    
    def _start_ip_camera(self):
        """IP камера (смартфон)"""
        ip_url = "http://192.168.1.100:8080/video"
        self.cap = cv2.VideoCapture(ip_url)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open IP camera")
    
    def read(self):
        """Прочитати кадр"""
        if not self.running:
            return False, None
        
        if self.picam:
            try:
                frame = self.picam.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return True, frame
            except Exception as e:
                return False, None
        
        elif self.cap:
            ret, frame = self.cap.read()
            return ret, frame
        
        return False, None
    
    def switch_source(self, new_source, device_id=0):
        """Переключити камеру"""
        if self.source == new_source and self.device_id == device_id and self.running:
            print(f"ℹ️ Already running {new_source} (ID: {device_id})")
            return

        print(f"🔄 Switching: {self.source} → {new_source}")
        self.stop()
        time.sleep(1.0)  # Increased delay for libcamera release
        
        self.source = new_source
        self.device_id = device_id
        self.start()
    
    def stop(self):
        """Зупинити камеру"""
        self.running = False
        if self.picam:
            try:
                self.picam.stop()
                if hasattr(self.picam, 'close'):
                    self.picam.close()
            except Exception as e:
                print(f"⚠️ Error stopping PiCamera: {e}")
            finally:
                self.picam = None
                # Force garbage collection
                import gc
                gc.collect()
        
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

# === ДЕТЕКТОР ===
class PlantDetector:
    """Детектор рослин з tracking"""
    
    def __init__(self, model_path):
        self.model = None
        self.model_path = model_path
        self.load_model()
        
        self.tracked_objects = {}
        self.next_id = 0
        self.total_detections = 0
        self.detection_history = deque(maxlen=100)
    
    def load_model(self):
        """Завантажити YOLO"""
        possible_paths = [self.model_path, 'best.pt', 'best.onnx', 'yolov8n.pt']
        
        model_file = None
        for path in possible_paths:
            if Path(path).exists():
                model_file = path
                break
        
        if not model_file:
            raise FileNotFoundError(f"Model not found! Tried: {possible_paths}")
        
        print(f"📥 Loading model: {model_file}")
        
        if IS_RASPBERRY_PI:
            torch.set_num_threads(4)
            os.environ['OMP_NUM_THREADS'] = '4'
        
        self.model = YOLO(model_file)
        self.model_path = model_file
        print(f"✅ Model: {len(self.model.names)} classes")
    
    def detect(self, frame):
        """Детекція"""
        if self.model is None or frame is None:
            return [], 0
        
        start_time = time.perf_counter()
        
        results = self.model(
            frame,
            imgsz=config.MODEL_IMGSZ,
            conf=config.CONFIDENCE_THRESHOLD,
            iou=config.IOU_THRESHOLD,
            verbose=False
        )
        
        inference_time = (time.perf_counter() - start_time) * 1000
        
        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                width = x2 - x1
                height = y2 - y1
                if width < config.MIN_OBJECT_SIZE or height < config.MIN_OBJECT_SIZE:
                    continue
                
                class_name = self.model.names.get(cls, f"class_{cls}")
                class_info = config.PLANT_CLASSES.get(cls, {})
                
                # Get English name for overlay if available
                class_name_en = class_info.get('name_en', class_name)
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': round(conf, 3),
                    'class_id': cls,
                    'class_name': class_name,
                    'class_name_en': class_name_en,
                    'category': class_info.get('category', 'unknown'),
                    'priority': class_info.get('priority', 'low'),
                    'description': class_info.get('description', ''),
                    'action': class_info.get('action', 'monitor'),
                    'color': class_info.get('color', [255, 255, 0]),
                    'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                    'area': int(width * height),
                    'width': int(width),
                    'height': int(height),
                    'timestamp': datetime.now().isoformat()
                }
                
                detections.append(detection)
        
        if config.ENABLE_TRACKING:
            detections = self.track_objects(detections)
        
        self.total_detections += len(detections)
        self.detection_history.append({
            'timestamp': time.time(),
            'count': len(detections),
            'inference_ms': inference_time
        })
        
        return detections, inference_time
    
    def track_objects(self, detections):
        """Tracking з IoU"""
        current_objects = {}
        
        for det in detections:
            bbox = det['bbox']
            best_iou = 0
            best_id = None
            
            for obj_id, prev_bbox in self.tracked_objects.items():
                iou = self.calculate_iou(bbox, prev_bbox)
                if iou > best_iou and iou > 0.3:
                    best_iou = iou
                    best_id = obj_id
            
            if best_id is not None:
                det['track_id'] = best_id
                current_objects[best_id] = bbox
            else:
                det['track_id'] = self.next_id
                current_objects[self.next_id] = bbox
                self.next_id += 1
        
        self.tracked_objects = current_objects
        return detections
    
    @staticmethod
    def calculate_iou(box1, box2):
        """IoU calculation"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0

# === ВІЗУАЛІЗАЦІЯ ===
class Visualizer:
    """Візуалізація детекцій"""
    
    @staticmethod
    def draw_detections(frame, detections):
        """Малювання bbox"""
        vis_frame = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            color = tuple(det['color'][::-1])  # RGB→BGR
            conf = det['confidence']
            class_name = det['class_name']
            track_id = det.get('track_id', '')
            priority = det['priority']
            
            # Товщина залежить від пріоритету
            thickness = 3 if priority == 'critical' else 2
            
            # Box
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Label
            # Use English name for video overlay to avoid encoding issues
            label_text = det.get('class_name_en', class_name)
            label = f"{label_text} {conf:.2f}"
            if track_id != '':
                label += f" #{track_id}"
            
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            
            cv2.rectangle(
                vis_frame,
                (x1, y1 - label_h - baseline - 5),
                (x1 + label_w, y1),
                color,
                -1
            )
            
            cv2.putText(
                vis_frame, label, (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA
            )
            
            # Центр
            cx, cy = det['center']
            cv2.circle(vis_frame, (cx, cy), 4, color, -1)
            cv2.circle(vis_frame, (cx, cy), 6, (255, 255, 255), 1)
            
            # Координати
            coord_text = f"({cx},{cy})"
            cv2.putText(
                vis_frame, coord_text, (cx + 8, cy - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA
            )
        
        return vis_frame

# === БАЗА ДАНИХ ===
class Database:
    """SQLite БД"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Ініціалізація"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY, timestamp TEXT, class_id INTEGER,
            class_name TEXT, category TEXT, confidence REAL,
            bbox_x1 INTEGER, bbox_y1 INTEGER, bbox_x2 INTEGER, bbox_y2 INTEGER,
            center_x INTEGER, center_y INTEGER, area INTEGER, track_id INTEGER,
            priority TEXT, action TEXT
        )''')
        
        conn.commit()
        conn.close()
    
    def save_detection(self, det):
        """Зберегти детекцію"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO detections VALUES (
                NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )''', (
                det['timestamp'], det['class_id'], det['class_name'],
                det['category'], det['confidence'],
                det['bbox'][0], det['bbox'][1], det['bbox'][2], det['bbox'][3],
                det['center'][0], det['center'][1], det['area'],
                det.get('track_id', -1), det['priority'], det['action']
            ))
            conn.commit()
            conn.close()
        except:
            pass

# === ГЛОБАЛЬНІ ЗМІННІ ===
camera = None
detector = None
current_frame = None
current_detections = []
frame_lock = threading.Lock()
color_fix_enabled = False  # Global flag for color fix

stats = {
    'fps': 0,
    'detections': 0,
    'inference_ms': 0,
    'total_processed': 0,
    'camera_source': 'none'
}

# Робот контролер
try:
    from robot_controller import RobotController
    robot = None
    robot_enabled = False
except ImportError:
    print("⚠️  robot_controller.py not found - robot control disabled")
    robot = None
    robot_enabled = False

# Flask app
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

db = Database(config.DB_PATH) if config.ENABLE_DATABASE else None

# === ОБРОБКА КАДРІВ ===
def process_frames():
    """Головний цикл"""
    global current_frame, current_detections, stats, color_fix_enabled
    
    frame_count = 0
    start_time = time.time()
    
    print("🎥 Processing started...")
    
    while True:
        try:
            frame = None
            if camera and camera.running:
                ret, frame = camera.read()
                if not ret:
                    frame = None
            
            if frame is None:
                # Create dummy frame
                frame = np.zeros((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8)
                cv2.putText(frame, "NO CAMERA SIGNAL", (50, config.CAMERA_HEIGHT//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                time.sleep(0.1)
            
            frame_count += 1
            stats['total_processed'] = frame_count
            stats['camera_source'] = camera.current_source if camera else "none"
            
            should_detect = (frame_count % config.PROCESS_EVERY_N_FRAMES == 0)
            
            if should_detect and frame is not None:
                detections, inference_time = detector.detect(frame)
                stats['detections'] = len(detections)
                stats['inference_ms'] = int(inference_time)
                
                if db:
                    for det in detections:
                        db.save_detection(det)
                
                # Add robot position to detections update
                robot_pos = {'x': 0, 'y': 0, 'heading': 0}
                if robot and robot_enabled:
                    robot_pos = robot.get_position()

                socketio.emit('detections_update', {
                    'count': len(detections),
                    'detections': [
                        {k: v for k, v in d.items() if k != 'timestamp'} 
                        for d in detections
                    ],
                    'robot_position': robot_pos
                })
            else:
                detections = current_detections
            
            vis_frame = Visualizer.draw_detections(frame, detections)
            
            # Apply color fix if enabled (Swap Red and Blue channels)
            if color_fix_enabled:
                vis_frame = cv2.cvtColor(vis_frame, cv2.COLOR_BGR2RGB)

            elapsed = time.time() - start_time
            if elapsed > 0:
                stats['fps'] = frame_count / elapsed
            
            with frame_lock:
                current_frame = vis_frame
                if should_detect:
                    current_detections = detections
        
        except Exception as e:
            print(f"⚠️  Error in process_frames: {e}")
            time.sleep(1)

# === FLASK ROUTES ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            with frame_lock:
                if current_frame is not None:
                    encode_param = [
                        int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY,
                        int(cv2.IMWRITE_JPEG_OPTIMIZE), 1
                    ]
                    _, buffer = cv2.imencode('.jpg', current_frame, encode_param)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1.0 / config.STREAM_FPS)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def get_stats():
    system_stats = {}
    if IS_RASPBERRY_PI:
        try:
            system_stats = {
                'cpu': psutil.cpu_percent(interval=0.1),
                'memory': psutil.virtual_memory().percent,
                'temp': 0
            }
        except:
            pass
    
    return jsonify({
        **stats,
        'system': system_stats,
        'platform': 'Raspberry Pi' if IS_RASPBERRY_PI else 'PC',
        'model': detector.model_path if detector else 'none',
        'total_detections': detector.total_detections if detector else 0,
        'config': {
            'confidence': config.CONFIDENCE_THRESHOLD,
            'iou': config.IOU_THRESHOLD,
            'imgsz': config.MODEL_IMGSZ
        }
    })

@app.route('/api/detections')
def get_detections():
    return jsonify({'detections': current_detections})

@app.route('/api/camera/switch', methods=['POST'])
def switch_camera():
    data = request.json
    source = data.get('source', 'auto')
    device_id = data.get('device_id', 0)
    
    if camera:
        try:
            camera.switch_source(source, device_id)
            return jsonify({'success': True, 'source': source})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'No camera'})

@app.route('/api/camera/color_fix', methods=['POST'])
def toggle_color_fix():
    global color_fix_enabled
    color_fix_enabled = not color_fix_enabled
    return jsonify({'success': True, 'enabled': color_fix_enabled})

@app.route('/api/config/update', methods=['POST'])
def update_config():
    data = request.json
    
    if 'confidence' in data:
        config.CONFIDENCE_THRESHOLD = float(data['confidence'])
    
    if 'iou' in data:
        config.IOU_THRESHOLD = float(data['iou'])
    
    return jsonify({'success': True})

@app.route('/api/export/csv')
def export_csv():
    """Експорт детекцій у CSV"""
    if not db:
        return "Database disabled", 400
        
    try:
        import csv
        import io
        
        conn = sqlite3.connect(config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM detections ORDER BY timestamp DESC")
        rows = c.fetchall()
        
        # Get headers
        headers = [description[0] for description in c.description]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        
        conn.close()
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=detections_{int(time.time())}.csv"}
        )
    except Exception as e:
        return str(e), 500

@app.route('/api/system/control', methods=['POST'])
def system_control():
    """Керування живленням"""
    action = request.json.get('action')
    
    if not IS_RASPBERRY_PI:
        return jsonify({'success': False, 'error': 'Only available on Raspberry Pi'})
        
    if action == 'reboot':
        os.system('sudo reboot')
        return jsonify({'success': True, 'message': 'Rebooting...'})
    elif action == 'shutdown':
        os.system('sudo shutdown -h now')
        return jsonify({'success': True, 'message': 'Shutting down...'})
        
    return jsonify({'success': False, 'error': 'Invalid action'})

# === ROBOT CONTROL API ===
@app.route('/robot')
def robot_page():
    """Сторінка керування роботом"""
    return render_template('robot_control.html')

@app.route('/api/robot/connect', methods=['POST'])
def robot_connect():
    """Підключитись до ESP32"""
    global robot, robot_enabled, patrol
    
    if robot is None:
        data = request.json or {}
        port = data.get('port', '/dev/ttyUSB0')
        
        try:
            robot = RobotController(port=port)
            if robot.connect():
                robot_enabled = True
                
                # Ініціалізація патруля при підключенні робота
                if patrol is None:
                    patrol = PatrolController(robot)
                    register_patrol_routes(app, patrol)
                    print("🗺️ Patrol system initialized")
                
                return jsonify({'success': True, 'port': port})
            else:
                return jsonify({'success': False, 'error': 'Connection failed'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': True, 'message': 'Already connected'})

@app.route('/api/robot/disconnect', methods=['POST'])
def robot_disconnect():
    """Відключитись від ESP32"""
    global robot, robot_enabled
    
    if robot:
        robot.disconnect()
        robot = None
        robot_enabled = False
    
    return jsonify({'success': True})

@app.route('/api/robot/move', methods=['POST'])
def robot_move():
    """Керування рухом"""
    if not robot or not robot_enabled:
        return jsonify({'success': False, 'error': 'Robot not connected'})
    
    data = request.json
    speed = data.get('speed', 0)
    turn = data.get('turn', 0)
    
    robot.move(speed=speed, turn=turn)
    return jsonify({'success': True, 'speed': speed, 'turn': turn})

@app.route('/api/robot/stop', methods=['POST'])
def robot_stop():
    """Зупинити робота"""
    if not robot or not robot_enabled:
        return jsonify({'success': False, 'error': 'Robot not connected'})
    
    robot.stop()
    return jsonify({'success': True})

@app.route('/api/robot/weed', methods=['POST'])
def robot_weed():
    """Прополювання"""
    if not robot or not robot_enabled:
        return jsonify({'success': False, 'error': 'Robot not connected'})
    
    data = request.json
    action = data.get('action', 'pulse')
    
    if action == 'pulse':
        robot.weed_pulse()
    elif action == 'activate':
        robot.weed_activate()
    elif action == 'deactivate':
        robot.weed_deactivate()
    elif action == 'servo':
        angle = data.get('angle', 90)
        robot.set_servo(angle)
    
    return jsonify({'success': True, 'action': action})

@app.route('/api/robot/auto_weed', methods=['POST'])
def robot_auto_weed():
    """Автоматичне прополювання на координатах детекції"""
    if not robot or not robot_enabled:
        return jsonify({'success': False, 'error': 'Robot not connected'})
    
    data = request.json
    x = data.get('x', 0)
    y = data.get('y', 0)
    
    # Центр камери
    camera_center_x = config.CAMERA_WIDTH // 2
    camera_center_y = config.CAMERA_HEIGHT // 2
    
    robot.weed_at_position(x, y, camera_center_x, camera_center_y)
    
    return jsonify({'success': True, 'x': x, 'y': y})

@app.route('/api/robot/status')
def robot_status():
    """Статус робота"""
    if robot and robot_enabled:
        status = robot.get_status()
        status['connected'] = True
        status['position'] = robot.get_position()
        return jsonify(status)
    else:
        return jsonify({'connected': False, 'robot_enabled': robot_enabled})

@app.route('/api/map/reset', methods=['POST'])
def reset_map():
    if robot and robot_enabled:
        robot.reset_position()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/snapshot', methods=['POST'])
def take_snapshot():
    """Зробити знімок поточного кадру"""
    global current_frame
    
    if current_frame is None:
        return jsonify({'success': False, 'error': 'No frame available'})
    
    try:
        # Create directory if not exists
        snapshot_dir = Path('web/static/snapshots')
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.jpg"
        filepath = snapshot_dir / filename
        
        # Save image
        with frame_lock:
            cv2.imwrite(str(filepath), current_frame)
            
        return jsonify({
            'success': True,
            'url': f"/static/snapshots/{filename}",
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@socketio.on('connect')
def handle_connect():
    print(f"📱 Client: {request.sid}")
    emit('connection_established', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"📱 Disconnected: {request.sid}")

# === MAIN ===
def main():
    global camera, detector, patrol
    
    print("\n" + "="*70)
    print("🌾 ПРОФЕСІЙНА СИСТЕМА ДЕТЕКЦІЇ РОСЛИН v2.0")
    print("="*70)
    print(f"Platform: {'Raspberry Pi' if IS_RASPBERRY_PI else 'PC'}")
    print(f"Model: {config.MODEL_PATH}")
    print(f"Camera: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
    print(f"Detection: imgsz={config.MODEL_IMGSZ}, conf={config.CONFIDENCE_THRESHOLD}")
    print("="*70 + "\n")
    
    try:
        print("📥 Loading model...")
        detector = PlantDetector(config.MODEL_PATH)
        
        print("📷 Starting camera...")
        try:
            camera = UniversalCamera(source=config.CAMERA_TYPE, device_id=config.CAMERA_DEVICE)
            camera.start()
        except Exception as e:
            print(f"❌ Camera init failed: {e}")
            print("⚠️  System starting without camera...")
            camera = None
        
        print("🚀 Starting processing...")
        processing_thread = threading.Thread(target=process_frames, daemon=True)
        processing_thread.start()

        # Запуск потоку патрулювання
        def patrol_loop():
            while True:
                if patrol and patrol.is_patrolling:
                    patrol.patrol_step()
                time.sleep(0.1)
        
        patrol_thread = threading.Thread(target=patrol_loop, daemon=True)
        patrol_thread.start()
        
        print(f"\n✅ System ready!")
        print(f"📱 Open: http://localhost:{config.WEB_PORT}")
        if IS_RASPBERRY_PI:
            print(f"📱 Remote: http://raspberrypi.local:{config.WEB_PORT}")
        print("\n💡 Cameras: webcam, picamera, ip")
        print("💡 Switch via web interface\n")
        
        socketio.run(
            app,
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=False,
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
        if camera:
            camera.stop()
        print("✅ Stopped\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if camera:
            camera.stop()

if __name__ == '__main__':
    main()
