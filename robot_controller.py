#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚜 КОНТРОЛЕР РОБОТА - Raspberry Pi
Зв'язок з ESP32 через Serial + Управління роботом
"""
import serial
import json
import time
import threading
from collections import deque

class RobotController:
    """Контролер для керування роботом через ESP32"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        Args:
            port: Serial порт (Linux: /dev/ttyUSB0, Windows: COM3)
            baudrate: Швидкість (115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        
        # Поточний стан
        self.current_status = {}
        self.response_queue = deque(maxlen=50)
        
        # Thread для читання
        self.reading_thread = None
        self.running = False
        
        # Odometry (Virtual)
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0  # Degrees (0 = North/Forward)
        self.last_update = time.time()
        self.current_speed = 0
        self.current_turn = 0
        
    def connect(self):
        """Підключитись до ESP32"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Дати час на ініціалізацію
            
            self.connected = True
            self.running = True
            
            # Запустити thread для читання
            self.reading_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.reading_thread.start()
            
            # Start odometry thread
            self.odometry_thread = threading.Thread(target=self._update_odometry, daemon=True)
            self.odometry_thread.start()
            
            print(f"✅ Connected to ESP32 on {self.port}")
            
            # Ping test
            response = self.ping()
            if response:
                print(f"🤖 Robot status: {response}")
                return True
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def _update_odometry(self):
        """Update virtual position based on speed and time"""
        import math
        while self.running:
            dt = time.time() - self.last_update
            self.last_update = time.time()
            
            if self.current_speed != 0 or self.current_turn != 0:
                # Simple differential drive approximation
                # Speed is roughly cm/s (calibrated needed)
                # Turn is roughly deg/s
                
                # Calibration constants (Adjust these!)
                SPEED_FACTOR = 0.5  # cm per unit speed per second
                TURN_FACTOR = 1.0   # degrees per unit turn per second
                
                v = self.current_speed * SPEED_FACTOR
                w = self.current_turn * TURN_FACTOR
                
                # Update heading
                self.heading += w * dt
                self.heading %= 360
                
                # Update position
                rad = math.radians(self.heading)
                self.x += v * math.sin(rad) * dt
                self.y += v * math.cos(rad) * dt
                
            time.sleep(0.1)

    def get_position(self):
        """Get current virtual position"""
        return {'x': self.x, 'y': self.y, 'heading': self.heading}

    def reset_position(self):
        """Reset position to (0,0)"""
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0

    def disconnect(self):
        """Відключитись"""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
        print("🔌 Disconnected from ESP32")
    
    def _read_loop(self):
        """Thread для читання відповідей від ESP32"""
        while self.running and self.serial:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.current_status.update(data)
                            self.response_queue.append(data)
                            
                            # Виводити важливі повідомлення
                            if 'error' in data:
                                print(f"⚠️  Robot error: {data['error']}")
                            elif 'status' in data and data['status'] != 'moving':
                                print(f"🤖 Robot: {data['status']}")
                                
                        except json.JSONDecodeError:
                            print(f"📡 Raw: {line}")
            except Exception as e:
                if self.running:
                    print(f"❌ Read error: {e}")
            
            time.sleep(0.01)
    
    def _send_command(self, command):
        """Відправити команду на ESP32"""
        if not self.connected or not self.serial:
            print("❌ Not connected to ESP32")
            return False
        
        try:
            json_str = json.dumps(command)
            self.serial.write((json_str + '\n').encode('utf-8'))
            self.serial.flush()
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    # === КОМАНДИ РУХУ ===
    
    def move(self, speed=0, turn=0):
        """
        Рух робота
        Args:
            speed: -100 (назад) до 100 (вперед)
            turn: -100 (ліворуч) до 100 (праворуч)
        """
        self.current_speed = int(speed)
        self.current_turn = int(turn)
        
        return self._send_command({
            'cmd': 'move',
            'speed': int(speed),
            'turn': int(turn)
        })
    
    def stop(self):
        """Зупинити робота"""
        self.current_speed = 0
        self.current_turn = 0
        return self._send_command({'cmd': 'stop'})
    
    def forward(self, speed=50):
        """Вперед"""
        return self.move(speed=speed, turn=0)
    
    def backward(self, speed=50):
        """Назад"""
        return self.move(speed=-speed, turn=0)
    
    def turn_left(self, turn_amount=50):
        """Поворот наліво"""
        return self.move(speed=0, turn=-turn_amount)
    
    def turn_right(self, turn_amount=50):
        """Поворот направо"""
        return self.move(speed=0, turn=turn_amount)
    
    def rotate(self, direction='left', speed=50):
        """Обертання на місці"""
        if direction == 'left':
            return self.move(speed=-speed, turn=-100)
        else:
            return self.move(speed=-speed, turn=100)
    
    # === КОМАНДИ ПРОПОЛЮВАННЯ ===
    
    def weed_activate(self):
        """Активувати прополювач"""
        return self._send_command({
            'cmd': 'weed',
            'action': 'activate'
        })
    
    def weed_deactivate(self):
        """Деактивувати прополювач"""
        return self._send_command({
            'cmd': 'weed',
            'action': 'deactivate'
        })
    
    def weed_pulse(self):
        """Швидкий удар прополювачем"""
        return self._send_command({
            'cmd': 'weed',
            'action': 'pulse'
        })
    
    def set_servo(self, angle):
        """
        Встановити кут сервоприводу
        Args:
            angle: 0-180 градусів
        """
        return self._send_command({
            'cmd': 'servo',
            'angle': int(angle)
        })
    
    # === АВТОМАТИЧНЕ ПРОПОЛЮВАННЯ ===
    
    def weed_at_position(self, x, y, camera_center_x, camera_center_y):
        """
        Прополоти на координатах детекції
        Args:
            x, y: координати бур'яну на кадрі
            camera_center_x, camera_center_y: центр камери
        """
        # Обчислити зміщення
        offset_x = x - camera_center_x
        offset_y = y - camera_center_y
        
        print(f"🎯 Weeding at ({x}, {y}), offset: ({offset_x}, {offset_y})")
        
        # Тут можна додати логіку позиціонування робота
        # Наприклад, якщо бур'ян зліва - повернути ліворуч
        
        if abs(offset_x) > 50:  # Поріг для повороту
            if offset_x < 0:
                self.turn_left(30)
                time.sleep(0.5)
            else:
                self.turn_right(30)
                time.sleep(0.5)
        
        # Прополоти
        self.weed_pulse()
        time.sleep(1)
        
        return True
    
    # === УТИЛІТИ ===
    
    def ping(self):
        """Перевірити зв'язок"""
        self._send_command({'cmd': 'ping'})
        time.sleep(0.1)
        return self.current_status.get('status') == 'pong'
    
    def enable_motors(self, state=True):
        """Увімкнути/вимкнути мотори"""
        return self._send_command({
            'cmd': 'enable',
            'state': state
        })
    
    def get_status(self):
        """Отримати поточний статус"""
        return self.current_status.copy()
    
    def get_last_responses(self, n=10):
        """Отримати останні відповіді"""
        return list(self.response_queue)[-n:]

# === ТЕСТ ===
if __name__ == '__main__':
    import sys
    
    print("🚜 Robot Controller Test")
    print("="*60)
    
    # Визначити порт
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        import platform
        if platform.system() == 'Windows':
            port = 'COM3'  # Змініть на ваш COM порт
        else:
            port = '/dev/ttyUSB0'  # Для Linux/Pi
    
    print(f"Connecting to {port}...")
    
    # Створити контролер
    robot = RobotController(port=port)
    
    # Підключитись
    if not robot.connect():
        print("❌ Failed to connect!")
        sys.exit(1)
    
    try:
        print("\n🎮 Testing robot control...")
        print("Commands: w=forward, s=backward, a=left, d=right, space=stop, q=quit")
        print("         p=weed pulse, [=servo left, ]=servo right\n")
        
        import keyboard  # pip install keyboard
        
        servo_angle = 90
        
        while True:
            if keyboard.is_pressed('w'):
                robot.forward(50)
                print("↑ Forward")
            elif keyboard.is_pressed('s'):
                robot.backward(50)
                print("↓ Backward")
            elif keyboard.is_pressed('a'):
                robot.turn_left(50)
                print("← Left")
            elif keyboard.is_pressed('d'):
                robot.turn_right(50)
                print("→ Right")
            elif keyboard.is_pressed('space'):
                robot.stop()
                print("⏹  Stop")
            elif keyboard.is_pressed('p'):
                robot.weed_pulse()
                print("🌾 Weed pulse!")
                time.sleep(0.5)
            elif keyboard.is_pressed('['):
                servo_angle = max(0, servo_angle - 10)
                robot.set_servo(servo_angle)
                print(f"◀ Servo: {servo_angle}°")
                time.sleep(0.2)
            elif keyboard.is_pressed(']'):
                servo_angle = min(180, servo_angle + 10)
                robot.set_servo(servo_angle)
                print(f"▶ Servo: {servo_angle}°")
                time.sleep(0.2)
            elif keyboard.is_pressed('q'):
                print("Quitting...")
                break
            
            time.sleep(0.1)
    
    except ImportError:
        print("\n⚠️  'keyboard' module not installed")
        print("Run: pip install keyboard")
        print("\nManual test:")
        
        print("\n1. Forward 2 sec...")
        robot.forward(50)
        time.sleep(2)
        
        print("2. Stop...")
        robot.stop()
        time.sleep(1)
        
        print("3. Backward 2 sec...")
        robot.backward(50)
        time.sleep(2)
        
        print("4. Stop...")
        robot.stop()
        time.sleep(1)
        
        print("5. Turn left...")
        robot.turn_left(50)
        time.sleep(2)
        
        print("6. Turn right...")
        robot.turn_right(50)
        time.sleep(2)
        
        print("7. Stop...")
        robot.stop()
        time.sleep(1)
        
        print("8. Weed pulse...")
        robot.weed_pulse()
        time.sleep(2)
        
        print("\n✅ Test complete!")
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
    
    finally:
        robot.stop()
        robot.disconnect()
        print("✅ Done!")
