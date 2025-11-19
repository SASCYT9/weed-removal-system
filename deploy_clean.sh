#!/bin/bash
# 🚀 CLEAN DEPLOYMENT SCRIPT - Only essential files

PI_USER="pi"
PI_HOST="raspberrypi.local"
PI_DIR="/home/pi/weed-system"

echo "════════════════════════════════════════════════════════"
echo "🚀 DEPLOYING CLEAN WEED DETECTION SYSTEM"
echo "════════════════════════════════════════════════════════"

# [1/6] Stop old process
echo "[1/6] Stopping old processes..."
ssh ${PI_USER}@${PI_HOST} "pkill -f app.py || true"
echo " -> Stopped."

# [2/6] Clean old installation
echo "[2/6] Cleaning old installation..."
ssh ${PI_USER}@${PI_HOST} "rm -rf ${PI_DIR}"
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_DIR}"
echo " -> Cleaned."

# [3/6] Create minimal archive (ONLY ESSENTIAL FILES)
echo "[3/6] Creating minimal archive..."
TEMP_DIR=$(mktemp -d)

# Copy only essential files
mkdir -p ${TEMP_DIR}/web
mkdir -p ${TEMP_DIR}/config
mkdir -p ${TEMP_DIR}/docs

cp app.py ${TEMP_DIR}/
cp robot_controller.py ${TEMP_DIR}/
cp requirements.txt ${TEMP_DIR}/
cp -r web/* ${TEMP_DIR}/web/
cp -r config/* ${TEMP_DIR}/config/
cp -r docs/* ${TEMP_DIR}/docs/

# Copy model if exists
if [ -f "best.pt" ]; then
    cp best.pt ${TEMP_DIR}/
elif [ -f "best.onnx" ]; then
    cp best.onnx ${TEMP_DIR}/
elif [ -f "yolov8n.pt" ]; then
    cp yolov8n.pt ${TEMP_DIR}/
fi

# Create archive
cd ${TEMP_DIR}
tar -czf /tmp/weed-system-clean.tar.gz .
cd -
rm -rf ${TEMP_DIR}

echo " -> Archive created: $(du -h /tmp/weed-system-clean.tar.gz | cut -f1)"

# [4/6] Upload to Pi
echo "[4/6] Uploading to Raspberry Pi..."
scp /tmp/weed-system-clean.tar.gz ${PI_USER}@${PI_HOST}:${PI_DIR}/
echo " -> Uploaded."

# [5/6] Extract and setup
echo "[5/6] Extracting and setting up..."
ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /home/pi/weed-system
tar -xzf weed-system-clean.tar.gz
rm weed-system-clean.tar.gz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

echo " -> Setup complete."
EOF

# [6/6] Start server
echo "[6/6] Starting server..."
ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /home/pi/weed-system
source venv/bin/activate
nohup python3 app.py > server.log 2>&1 &
sleep 3
PID=$(pgrep -f app.py | tail -1)
echo " -> Server started with PID: ${PID}"
EOF

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📱 Access web interface:"
echo "   http://raspberrypi.local:5000"
echo ""
echo "📋 Check logs:"
echo "   ssh ${PI_USER}@${PI_HOST} 'tail -f /home/pi/weed-system/server.log'"
echo ""
echo "⏹️  Stop server:"
echo "   ssh ${PI_USER}@${PI_HOST} 'pkill -f app.py'"
echo ""
