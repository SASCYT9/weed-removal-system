"""MQTT client for telemetry data transmission."""

import json
import paho.mqtt.client as mqtt
from typing import Any, Callable, Optional
from threading import Lock
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class MQTTClient:
    """MQTT client for robot telemetry."""

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        topic_prefix: str = "weed_robot",
        keepalive: int = 60,
        username: str = None,
        password: str = None
    ):
        """
        Initialize MQTT client.

        Args:
            broker: MQTT broker address
            port: MQTT broker port
            topic_prefix: Prefix for all topics
            keepalive: Keepalive interval in seconds
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.keepalive = keepalive

        self.client = mqtt.Client()
        self._connected = False
        self._lock = Lock()

        # Set credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        logger.info(f"MQTT Client initialized: {broker}:{port}")

    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection."""
        if rc == 0:
            self._connected = True
            logger.info("Connected to MQTT broker")

            # Subscribe to command topics
            self.subscribe("command/#")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection."""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback for received messages."""
        logger.debug(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    def publish(self, topic: str, data: Any, qos: int = 0, retain: bool = False):
        """
        Publish data to MQTT topic.

        Args:
            topic: Topic name (will be prefixed)
            data: Data to publish (will be JSON serialized if dict)
            qos: Quality of Service (0, 1, or 2)
            retain: Retain message flag
        """
        if not self._connected:
            logger.warning("Not connected to MQTT broker")
            return

        full_topic = f"{self.topic_prefix}/{topic}"

        # Serialize data to JSON if it's a dict
        if isinstance(data, dict):
            payload = json.dumps(data)
        else:
            payload = str(data)

        try:
            result = self.client.publish(full_topic, payload, qos=qos, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {full_topic}")
            else:
                logger.error(f"Failed to publish to {full_topic}, error code: {result.rc}")

        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")

    def subscribe(self, topic: str, qos: int = 0):
        """
        Subscribe to MQTT topic.

        Args:
            topic: Topic name (will be prefixed)
            qos: Quality of Service (0, 1, or 2)
        """
        full_topic = f"{self.topic_prefix}/{topic}"
        self.client.subscribe(full_topic, qos=qos)
        logger.info(f"Subscribed to {full_topic}")

    def publish_status(self, status: dict):
        """Publish robot status."""
        self.publish("status", status, qos=1)

    def publish_gps(self, gps_data: dict):
        """Publish GPS data."""
        self.publish("gps", gps_data)

    def publish_detection(self, detections: list):
        """Publish detection results."""
        self.publish("detections", {"detections": detections})

    def publish_telemetry(self, telemetry: dict):
        """Publish general telemetry data."""
        self.publish("telemetry", telemetry)

    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
