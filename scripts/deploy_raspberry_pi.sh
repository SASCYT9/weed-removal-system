#!/bin/bash
# Quick deployment script for Raspberry Pi

echo "🤖 WeedBot Deployment Script"
echo "=============================="

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install dependencies
echo "📥 Installing system dependencies..."
sudo apt install -y python3-pip mosquitto mosquitto-clients

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Start MQTT broker
echo "🔌 Starting MQTT broker..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Test configuration
echo "✅ Testing configuration..."
python3 -c "import yaml; yaml.safe_load(open('config/config.yaml'))" && echo "Config OK" || echo "Config ERROR"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "To start the robot:"
echo "  python3 main.py"
echo ""
echo "To enable autostart:"
echo "  sudo cp deploy/weedbot.service /etc/systemd/system/"
echo "  sudo systemctl enable weedbot"
echo "  sudo systemctl start weedbot"
echo ""
echo "Web interface will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
