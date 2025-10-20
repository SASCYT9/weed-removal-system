"""Flask web server for robot monitoring."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import time
from typing import Dict, Any
import os
from PIL import Image, ImageDraw, ImageFont
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class WebServer:
    """Web server for robot monitoring and control."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False
    ):
        """
        Initialize web server.

        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug

        # Create Flask app
        self.app = Flask(
            __name__,
            template_folder="../../web/templates",
            static_folder="../../web/static"
        )

        # Create SocketIO instance
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Robot state
        self.robot_state = {
            'status': 'idle',
            'position': {'x': 0, 'y': 0, 'heading': 0},
            'gps': None,
            'detections': [],
            'telemetry': {},
            'statistics': {
                'weeds_detected': 0,
                'weeds_removed': 0,
                'distance_traveled': 0.0
            }
        }

        # Setup routes
        self._setup_routes()

        # Ensure PWA static assets exist (icons, screenshots)
        try:
            self._ensure_pwa_assets()
        except Exception as e:
            logger.warning(f"Failed to ensure PWA assets: {e}")

        logger.info(f"Web server initialized on {host}:{port}")

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')

        @self.app.route('/api/status')
        def get_status():
            """Get robot status."""
            return jsonify(self.robot_state)

        @self.app.route('/api/command', methods=['POST'])
        def send_command():
            """Send command to robot."""
            data = request.get_json()
            command = data.get('command')

            logger.info(f"Received command: {command}")

            # Emit command via SocketIO
            self.socketio.emit('command', {'command': command})

            return jsonify({'success': True, 'command': command})

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info("Web client connected")
            emit('robot_state', self.robot_state)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Web client disconnected")

    def update_state(self, key: str, value: Any):
        """
        Update robot state.

        Args:
            key: State key
            value: State value
        """
        if key in self.robot_state:
            self.robot_state[key] = value

            # Broadcast update to connected clients
            self.socketio.emit('state_update', {key: value})

            logger.debug(f"State updated: {key}")

    def update_position(self, x: float, y: float, heading: float):
        """Update robot position."""
        self.robot_state['position'] = {
            'x': x,
            'y': y,
            'heading': heading
        }
        self.socketio.emit('position_update', self.robot_state['position'])

    def update_gps(self, gps_data: Dict):
        """Update GPS data."""
        self.robot_state['gps'] = gps_data
        self.socketio.emit('gps_update', gps_data)

    def update_detections(self, detections: list):
        """Update detection results."""
        self.robot_state['detections'] = detections
        self.robot_state['statistics']['weeds_detected'] = len(
            [d for d in detections if d.get('class_name') == 'weed']
        )
        self.socketio.emit('detections_update', detections)

    def update_telemetry(self, telemetry: Dict):
        """Update telemetry data."""
        self.robot_state['telemetry'] = telemetry
        self.socketio.emit('telemetry_update', telemetry)

    def increment_weeds_removed(self):
        """Increment weeds removed counter."""
        self.robot_state['statistics']['weeds_removed'] += 1
        self.socketio.emit('statistics_update', self.robot_state['statistics'])

    def run(self):
        """Run web server."""
        logger.info(f"Starting web server on {self.host}:{self.port}")
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            allow_unsafe_werkzeug=True
        )

    def run_in_background(self):
        """Run web server in background thread."""
        from threading import Thread

        thread = Thread(
            target=self.run,
            daemon=True
        )
        thread.start()
        logger.info("Web server started in background")

    def _ensure_pwa_assets(self):
        """Create required PWA icon and image assets if missing using Pillow."""
        base_static = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../web/static'))
        icons_dir = os.path.join(base_static, 'icons')
        images_dir = os.path.join(base_static, 'images')
        os.makedirs(icons_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        # Icon sizes to generate
        icon_specs = [
            (72, 'icon-72x72.png'),
            (96, 'icon-96x96.png'),
            (128, 'icon-128x128.png'),
            (144, 'icon-144x144.png'),
            (152, 'icon-152x152.png'),
            (192, 'icon-192x192.png'),
            (384, 'icon-384x384.png'),
            (512, 'icon-512x512.png'),
        ]

        def ensure_icon(size: int, name: str, label: str = 'WB', bg: tuple = (102, 126, 234)):
            path = os.path.join(icons_dir, name)
            if os.path.exists(path):
                return
            img = Image.new('RGBA', (size, size), bg + (255,))
            draw = ImageDraw.Draw(img)
            # Simple rounded rectangle background
            radius = int(size * 0.18)
            draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill=bg)
            # Add label text
            try:
                # Try to use a common system font; fallback to default
                font = ImageFont.truetype("arial.ttf", int(size * 0.38))
            except Exception:
                font = ImageFont.load_default()
            # Use textbbox instead of deprecated textsize
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.text(((size - text_w) / 2, (size - text_h) / 2), label, fill=(255, 255, 255, 255), font=font)
            img.save(path, format='PNG')
            logger.info(f"Generated PWA icon: {path}")

        for sz, fname in icon_specs:
            ensure_icon(sz, fname)

        # Badge and action icons
        if not os.path.exists(os.path.join(icons_dir, 'badge-72x72.png')):
            ensure_icon(72, 'badge-72x72.png', label='WB', bg=(118, 75, 162))
        if not os.path.exists(os.path.join(icons_dir, 'view.png')):
            ensure_icon(96, 'view.png', label='▶', bg=(76, 175, 80))
        if not os.path.exists(os.path.join(icons_dir, 'close.png')):
            ensure_icon(96, 'close.png', label='✕', bg=(244, 67, 54))
        if not os.path.exists(os.path.join(icons_dir, 'start.png')):
            ensure_icon(96, 'start.png', label='GO', bg=(76, 175, 80))
        if not os.path.exists(os.path.join(icons_dir, 'stop.png')):
            ensure_icon(96, 'stop.png', label='STOP', bg=(244, 67, 54))

        # Screenshot placeholder
        screenshot_path = os.path.join(images_dir, 'screenshot1.png')
        if not os.path.exists(screenshot_path):
            w, h = 540, 720
            img = Image.new('RGB', (w, h), (245, 247, 251))
            draw = ImageDraw.Draw(img)
            # Title bar
            draw.rectangle([(0, 0), (w, 72)], fill=(102, 126, 234))
            try:
                font_title = ImageFont.truetype('arial.ttf', 28)
                font_body = ImageFont.truetype('arial.ttf', 18)
            except Exception:
                font_title = ImageFont.load_default()
                font_body = ImageFont.load_default()
            draw.text((16, 20), 'Weed Removal Robot', fill=(255, 255, 255), font=font_title)
            # Content blocks
            y = 110
            for title, color in [('Статус', (255, 255, 255)), ('Позиція', (255, 255, 255)), ('Статистика', (255, 255, 255))]:
                draw.rounded_rectangle([(16, y), (w-16, y+120)], radius=12, fill=color, outline=(224,224,224))
                draw.text((32, y+16), title, fill=(51,51,51), font=font_body)
                y += 140
            img.save(screenshot_path, format='PNG')
            logger.info(f"Generated PWA screenshot: {screenshot_path}")
