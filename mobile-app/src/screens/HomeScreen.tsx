import React from 'react';
import {View, Text, StyleSheet, ScrollView} from 'react-native';
import StatusCard from '../components/StatusCard';
import DetectionFeed from '../components/DetectionFeed';

const HomeScreen = () => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>WeedBot • Головна</Text>
      <StatusCard />
      <DetectionFeed />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fb' },
  content: { padding: 16 },
  header: { fontSize: 20, fontWeight: '700', marginBottom: 12, color: '#333' },
});

export default HomeScreen;
