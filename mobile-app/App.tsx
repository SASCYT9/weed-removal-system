/**
 * Weed Removal Robot Mobile App
 * Main Application Entry Point
 */

import React, {useEffect, useState} from 'react';
import {StatusBar, StyleSheet, Platform, PermissionsAndroid} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import MainNavigator from './src/navigation/MainNavigator';
import {MQTTProvider} from './src/services/MQTTService';
import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure push notifications
PushNotification.configure({
  onNotification: function (notification) {
    console.log('NOTIFICATION:', notification);
  },
  permissions: {
    alert: true,
    badge: true,
    sound: true,
  },
  popInitialNotification: true,
  requestPermissions: Platform.OS === 'ios',
});

function App(): JSX.Element {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    requestPermissions();
    loadSettings();
  }, []);

  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          PermissionsAndroid.PERMISSIONS.CAMERA,
          PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
        ]);

        console.log('Permissions granted:', granted);
      } catch (err) {
        console.warn(err);
      }
    }
  };

  const loadSettings = async () => {
    try {
      const settings = await AsyncStorage.getItem('@robot_settings');
      if (settings) {
        console.log('Loaded settings:', JSON.parse(settings));
      }
      setIsReady(true);
    } catch (error) {
      console.error('Error loading settings:', error);
      setIsReady(true);
    }
  };

  if (!isReady) {
    return null; // TODO: Add splash screen
  }

  return (
    <SafeAreaProvider>
      <MQTTProvider>
        <NavigationContainer>
          <StatusBar
            barStyle="light-content"
            backgroundColor="#667eea"
            translucent={false}
          />
          <MainNavigator />
        </NavigationContainer>
      </MQTTProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;
