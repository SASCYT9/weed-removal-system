import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import HomeScreen from '../screens/HomeScreen';
import MapScreen from '../screens/MapScreen';
import ControlScreen from '../screens/ControlScreen';
import StatsScreen from '../screens/StatsScreen';
import SettingsScreen from '../screens/SettingsScreen';

const Tab = createBottomTabNavigator();

const MainNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#667eea',
        tabBarInactiveTintColor: '#999',
      }}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{title: '🏠 Головна'}} />
      <Tab.Screen name="Map" component={MapScreen} options={{title: '🗺️ Карта'}} />
      <Tab.Screen name="Control" component={ControlScreen} options={{title: '🎮 Керування'}} />
      <Tab.Screen name="Stats" component={StatsScreen} options={{title: '📊 Статистика'}} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{title: '⚙️ Налаштування'}} />
    </Tab.Navigator>
  );
};

export default MainNavigator;
