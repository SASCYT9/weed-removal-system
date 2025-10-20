import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import {sendRobotCommand} from '../services/APIService';

const ControlButton = ({label, command, color}: {label: string; command: string; color: string}) => (
  <TouchableOpacity style={[styles.btn, {backgroundColor: color}]} onPress={() => sendRobotCommand(command)}>
    <Text style={styles.btnText}>{label}</Text>
  </TouchableOpacity>
);

const ControlScreen = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.header}>Керування роботом</Text>
      <View style={styles.row}>
        <ControlButton label="Старт" command="start" color="#4caf50" />
        <ControlButton label="Пауза" command="pause" color="#ff9800" />
      </View>
      <View style={styles.row}>
        <ControlButton label="Стоп" command="stop" color="#f44336" />
        <ControlButton label="Скинути" command="reset" color="#2196f3" />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f5f7fb' },
  header: { fontSize: 18, fontWeight: '700', marginBottom: 12, color: '#333' },
  row: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  btn: { flex: 1, padding: 16, borderRadius: 10, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '700' },
});

export default ControlScreen;
