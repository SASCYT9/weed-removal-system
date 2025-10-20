# 📱 Weed Removal Robot - Mobile App

React Native мобільний додаток для керування роботом прополювання бур'янів.

## 🎯 Можливості

### ✅ Реалізовано в PWA (Веб-додаток)
- 🔴 Real-time статус робота
- 📍 GPS позиціонування
- 📊 Статистика та аналітика
- 🎮 Керування роботом (Start/Stop/Pause/Reset)
- 🔔 Push нотифікації
- 📶 Offline режим з синхронізацією
- 📱 Можна встановити на домашній екран
- 🌐 Працює на всіх платформах

### 🚀 Планується в React Native
- 📱 Нативний Android/iOS додаток
- 🗺️ Google Maps інтеграція
- 📷 Камера live stream
- 🔊 Голосові команди
- 📲 Кращі push notifications
- 🎨 Material Design 3 UI
- ⚡ Швидша продуктивність

## 🌐 PWA - Доступний зараз!

### Встановлення PWA

1. **На Android:**
   - Відкрийте Chrome: `http://<robot-ip>:5000`
   - Натисніть "📱 Встановити додаток"
   - Або: Меню → "Add to Home screen"

2. **На iOS:**
   - Відкрийте Safari: `http://<robot-ip>:5000`
   - Натисніть кнопку "Share"
   - Виберіть "Add to Home Screen"

3. **На Desktop:**
   - Chrome/Edge: іконка "Встановити" в адресному рядку
   - Або: Меню → "Install Weed Robot..."

### Функції PWA

✅ **Offline Mode**
- Працює без інтернету
- Кешування даних
- Синхронізація при відновленні з'єднання

✅ **Push Notifications**
- Сповіщення про події
- Статус робота
- Критичні попередження

✅ **Responsive Design**
- Адаптується під будь-який екран
- Працює на планшетах
- Desktop підтримка

✅ **Real-time Updates**
- WebSocket (SocketIO)
- Миттєві оновлення статусу
- Live детекції бур'янів

## 📦 React Native Setup (Для розробки)

### Системні вимоги

- Node.js 16+
- React Native CLI
- Android Studio (для Android)
- Xcode (для iOS, тільки на macOS)

### Встановлення

```bash
cd mobile-app

# Встановити залежності
npm install

# Android
npx react-native run-android

# iOS (тільки macOS)
npx react-native run-ios
```

### Build Release APK

```bash
cd mobile-app

# Генерувати release APK
cd android
./gradlew assembleRelease

# APK буде в:
# android/app/build/outputs/apk/release/app-release.apk
```

## 🎨 Структура Проекту

```
mobile-app/
├── src/
│   ├── screens/
│   │   ├── HomeScreen.tsx       # Головний екран
│   │   ├── MapScreen.tsx        # Карта GPS
│   │   ├── ControlScreen.tsx    # Керування
│   │   ├── StatsScreen.tsx      # Статистика
│   │   └── SettingsScreen.tsx   # Налаштування
│   │
│   ├── components/
│   │   ├── StatusCard.tsx       # Статус робота
│   │   ├── GPSIndicator.tsx     # GPS індикатор
│   │   ├── ControlPanel.tsx     # Панель керування
│   │   └── DetectionFeed.tsx    # Стрічка детекцій
│   │
│   ├── services/
│   │   ├── MQTTService.tsx      # MQTT клієнт
│   │   ├── APIService.tsx       # REST API
│   │   └── NotificationService.tsx  # Push notifications
│   │
│   ├── navigation/
│   │   └── MainNavigator.tsx    # Навігація
│   │
│   └── utils/
│       ├── colors.ts            # Кольори
│       └── constants.ts         # Константи
│
├── android/                     # Android проект
├── ios/                         # iOS проект
├── App.tsx                      # Entry point
└── package.json                 # Dependencies
```

## 🔧 Конфігурація

### Підключення до робота

Налаштуйте IP адресу робота в `src/utils/constants.ts`:

```typescript
export const ROBOT_CONFIG = {
  host: '192.168.1.100',  // IP вашого Raspberry Pi
  port: 5000,
  mqttPort: 1883,
  protocol: 'http'
};
```

## 📱 Екрани Додатку

### 1. Home Screen (Головна)
- Статус робота
- GPS позиція
- Статистика

### 2. Map Screen (Карта)
- Google Maps
- Траєкторія робота
- Позначки детекцій

### 3. Control Screen (Керування)
- Start/Stop/Pause
- Режими роботи
- Екстрене зупинення

### 4. Stats Screen (Статистика)
- Графіки продуктивності
- Історія детекцій
- Аналітика

### 5. Settings Screen (Налаштування)
- Підключення
- Нотифікації
- Теми

## 🔔 Push Notifications

### Типи сповіщень:

- 🟢 **Початок роботи** - робот почав операцію
- 🟡 **Детекція** - виявлено бур'яни
- 🔴 **Попередження** - GPS втрачений, низька батарея
- ⚫ **Зупинка** - робот зупинився

## 🎨 Теми

- 🌞 Light mode (за замовчуванням)
- 🌙 Dark mode
- 🎨 Custom colors

## 📊 MQTT Топіки

Додаток підписується на:

```
weed_robot/status          # Статус робота
weed_robot/gps             # GPS дані
weed_robot/detections      # Детекції
weed_robot/telemetry       # Телеметрія
```

Публікує в:

```
weed_robot/command         # Команди керування
```

## 🚀 Швидкий старт

### Для користувачів (PWA)

```bash
# 1. Запустіть Flask сервер на Raspberry Pi
python main.py

# 2. Відкрийте браузер на телефоні
http://<raspberry-pi-ip>:5000

# 3. Натисніть "Встановити додаток"
# Готово! Додаток на домашньому екрані
```

### Для розробників (React Native)

```bash
# 1. Клонувати репозиторій
git clone https://github.com/yourusername/weed-removal-system
cd weed-removal-system/mobile-app

# 2. Встановити залежності
npm install

# 3. Налаштувати Android emulator або підключити пристрій

# 4. Запустити
npm run android
```

## 📸 Screenshots

*(Додайте screenshots після створення)*

## 🔐 Безпека

- ✅ HTTPS підтримка
- ✅ Авторизація
- ✅ Шифрування даних
- ✅ Безпечне зберігання токенів

## 🐛 Troubleshooting

### PWA не встановлюється

1. Перевірте HTTPS (або localhost для тестування)
2. Перевірте manifest.json
3. Очистіть кеш браузера

### React Native помилки

```bash
# Очистити кеш
npm start -- --reset-cache

# Rebuild Android
cd android && ./gradlew clean && cd ..
npm run android
```

## 📝 TODO

- [ ] Завершити React Native UI
- [ ] Додати Google Maps
- [ ] Імплементувати voice commands
- [ ] Додати AR mode для візуалізації
- [ ] Multi-robot support
- [ ] Offline maps

## 💡 Рекомендація для дипломної роботи

**Використовуйте PWA** - він вже повністю функціональний і працює чудово!

React Native - це додаткова опція для покращеної native experience, але не обов'язкова для базової функціональності.

## 📞 Підтримка

Для питань створіть Issue на GitHub.

---

**🎓 Створено для дипломної роботи**
**Автономна система прополювання бур'янів**
