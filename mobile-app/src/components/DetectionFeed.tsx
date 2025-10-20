import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

const DetectionFeed = () => {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Детекції</Text>
      <Text style={styles.placeholder}>Немає останніх детекцій</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 2 },
  title: { fontWeight: '700', color: '#333', marginBottom: 8 },
  placeholder: { color: '#666' },
});

export default DetectionFeed;
