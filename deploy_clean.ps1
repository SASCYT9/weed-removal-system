# 🚀 CLEAN DEPLOYMENT SCRIPT - Only essential files (PowerShell)

$PI_USER = "pi"
$PI_HOST = "raspberrypi.local"
$PI_DIR = "/home/pi/weed-system"

Write-Host "═══════════════════════════════════════════════════════=" -ForegroundColor Cyan
Write-Host "🚀 DEPLOYING CLEAN WEED DETECTION SYSTEM" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════=" -ForegroundColor Cyan

# [1/7] Stop old process
Write-Host "[1/7] Stopping old processes..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "pkill -f app.py || true"
Write-Host " -> Stopped." -ForegroundColor Green

# [2/7] Clean old installation
Write-Host "[2/7] Cleaning old installation..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "rm -rf $PI_DIR"
ssh "$PI_USER@$PI_HOST" "mkdir -p $PI_DIR"
Write-Host " -> Cleaned." -ForegroundColor Green

# [3/7] Create minimal archive
Write-Host "[3/7] Creating minimal archive (ONLY ESSENTIAL FILES)..." -ForegroundColor Yellow

# Remove old archive if exists
if (Test-Path "weed-system-clean.tar.gz") {
    Remove-Item "weed-system-clean.tar.gz"
}

# Create archive with only essential files
$files = @(
    "app.py",
    "robot_controller.py",
    "requirements.txt",
    "web",
    "config",
    "docs"
)

# Add model if exists (already copied to current dir)
$modelFiles = @("best.pt", "best.onnx", "yolov8n.pt", "yolo11n.pt")
foreach ($model in $modelFiles) {
    if (Test-Path $model) {
        Write-Host "   Found model: $model" -ForegroundColor Green
        $files += $model
        break
    }
}

# Create tar.gz archive
tar -czf weed-system-clean.tar.gz $files

$archiveSize = (Get-Item "weed-system-clean.tar.gz").Length / 1MB
Write-Host " -> Archive created: $([math]::Round($archiveSize, 2)) MB" -ForegroundColor Green

# [4/7] Upload to Pi
Write-Host "[4/7] Uploading to Raspberry Pi..." -ForegroundColor Yellow
scp weed-system-clean.tar.gz "$PI_USER@${PI_HOST}:$PI_DIR/"
Write-Host " -> Uploaded." -ForegroundColor Green

# [5/7] Extract
Write-Host "[5/7] Extracting on Pi..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "cd $PI_DIR && tar -xzf weed-system-clean.tar.gz && rm weed-system-clean.tar.gz"
Write-Host " -> Extracted." -ForegroundColor Green

# [6/7] Setup environment and install dependencies
Write-Host "[6/7] Setting up environment..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "cd $PI_DIR && python3 -m venv --system-site-packages venv && source venv/bin/activate && pip install --upgrade pip setuptools wheel -q && pip install -r requirements.txt -q && echo 'Environment ready'"
Write-Host " -> Environment ready." -ForegroundColor Green

# [6.5/7] Create run wrapper script
Write-Host "[6.5/7] Creating run script..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "cat > $PI_DIR/run.sh << 'EOFRUN'
#!/bin/bash
cd $PI_DIR
export PYTHONPATH=/usr/lib/python3/dist-packages:\`$PYTHONPATH
source venv/bin/activate
python3 app.py
EOFRUN
chmod +x $PI_DIR/run.sh"
Write-Host " -> Run script created." -ForegroundColor Green

# [7/7] Start server
Write-Host "[7/7] Starting server..." -ForegroundColor Yellow
ssh "$PI_USER@$PI_HOST" "cd $PI_DIR && nohup ./run.sh > server.log 2>&1 & sleep 3 && pgrep -f app.py | tail -1"
Write-Host " -> Server started." -ForegroundColor Green

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════=" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════=" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Web interface: http://raspberrypi.local:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 View logs:" -ForegroundColor Cyan
Write-Host "   ssh $PI_USER@$PI_HOST 'tail -f $PI_DIR/server.log'" -ForegroundColor White
Write-Host ""
Write-Host "⏹️  Stop server:" -ForegroundColor Cyan
Write-Host "   ssh $PI_USER@$PI_HOST 'pkill -f app.py'" -ForegroundColor White
Write-Host ""

# Clean up local archive
Remove-Item "weed-system-clean.tar.gz" -ErrorAction SilentlyContinue
