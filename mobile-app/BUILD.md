# 📱 React Native Mobile App - Build Instructions

## Windows Build Setup

### Prerequisites

1. **Node.js 18 LTS**
   - Download: https://nodejs.org/
   - Verify: `node --version` (should be v18+)

2. **Android Studio**
   - Download: https://developer.android.com/studio
   - Install SDK Platform 33 (Android 13)
   - Install Android SDK Build-Tools
   - Create Virtual Device (emulator)

3. **Environment Variables**
   ```
   ANDROID_HOME = C:\Users\YourUsername\AppData\Local\Android\Sdk
   
   Add to PATH:
   %ANDROID_HOME%\platform-tools
   %ANDROID_HOME%\tools
   ```

### Quick Start

```powershell
# Install dependencies
cd mobile-app
npm install

# Start Metro bundler
npm start

# In another terminal - Run on Android
npm run android
```

### Build Release APK

```powershell
cd android
.\gradlew assembleRelease

# APK location:
# android\app\build\outputs\apk\release\app-release.apk
```

### Install on Phone

```powershell
# Connect phone via USB (enable USB debugging)
adb devices

# Install
adb install android\app\build\outputs\apk\release\app-release.apk
```

## Current Status

✅ **Working Features:**
- Navigation with 5 tabs (Home, Map, Control, Stats, Settings)
- REST API integration with Flask server
- Settings storage (robot IP/port)
- Control panel (Start/Stop/Pause/Reset commands)
- Status display

🚧 **TODO (for future enhancement):**
- MQTT real-time updates
- Google Maps integration
- Push notifications
- Camera live stream

## Configuration

Edit robot IP in `src/utils/constants.ts`:

```typescript
export const DEFAULT_SETTINGS = {
  host: '192.168.1.100',  // Your Raspberry Pi IP
  port: 5000,
  mqttPort: 1883,
};
```

Or configure in app Settings screen.

## Troubleshooting

**Metro bundler errors:**
```powershell
npm start -- --reset-cache
```

**Android build fails:**
```powershell
cd android
.\gradlew clean
cd ..
npm run android
```

**Module not found errors:**
```powershell
rm -rf node_modules
npm install
```

## For Thesis Demo

**Recommendation:** Use PWA instead of React Native for demo:
- ✅ Faster to setup
- ✅ Works on all platforms
- ✅ No app store approval
- ✅ All features working NOW

React Native app is a bonus but not required for basic functionality.
