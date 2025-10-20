import React, {useEffect, useState} from 'react';
import {View, Text, StyleSheet, TextInput, TouchableOpacity, Alert} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SettingsScreen = () => {
  const [host, setHost] = useState('192.168.1.100');
  const [port, setPort] = useState('5000');
  const [mqttPort, setMqttPort] = useState('1883');

  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem('@robot_settings');
        if (saved) {
          const s = JSON.parse(saved);
          setHost(s.host || host);
          setPort(String(s.port || port));
          setMqttPort(String(s.mqttPort || mqttPort));
        }
      } catch {}
    })();
  }, []);

  const save = async () => {
    const data = {host, port: Number(port), mqttPort: Number(mqttPort)};
    await AsyncStorage.setItem('@robot_settings', JSON.stringify(data));
    Alert.alert('Збережено', 'Налаштування оновлено');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Налаштування підключення</Text>
      <Text style={styles.label}>IP адреса робота</Text>
      <TextInput style={styles.input} value={host} onChangeText={setHost} placeholder="192.168.1.100" />
      <View style={{height: 8}} />
      <Text style={styles.label}>HTTP порт</Text>
      <TextInput style={styles.input} value={port} onChangeText={setPort} keyboardType="numeric" />
      <View style={{height: 8}} />
      <Text style={styles.label}>MQTT порт</Text>
      <TextInput style={styles.input} value={mqttPort} onChangeText={setMqttPort} keyboardType="numeric" />
      <TouchableOpacity style={styles.btn} onPress={save}>
        <Text style={styles.btnText}>Зберегти</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f5f7fb' },
  header: { fontSize: 18, fontWeight: '700', marginBottom: 12, color: '#333' },
  label: { color: '#555', marginBottom: 6, fontWeight: '600' },
  input: { backgroundColor: '#fff', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#e0e0e0' },
  btn: { marginTop: 16, backgroundColor: '#667eea', padding: 14, borderRadius: 10, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '700' },
});

export default SettingsScreen;
