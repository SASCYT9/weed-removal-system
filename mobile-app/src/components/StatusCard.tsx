import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

const StatusCard = () => {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Статус робота</Text>
      <View style={styles.row}><Text style={styles.key}>Статус:</Text><Text style={styles.val}>Очікування</Text></View>
      <View style={styles.row}><Text style={styles.key}>GPS:</Text><Text style={styles.val}>Немає сигналу</Text></View>
      <View style={styles.row}><Text style={styles.key}>Батарея:</Text><Text style={styles.val}>--</Text></View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 2 },
  title: { fontWeight: '700', color: '#333', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  key: { color: '#666', fontWeight: '600' },
  val: { color: '#333', fontWeight: '600' },
});

export default StatusCard;
