"""Flask web server for robot monitoring."""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import time
from typing import Dict, Any
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
