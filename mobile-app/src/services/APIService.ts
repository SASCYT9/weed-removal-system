import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

async function getBaseUrl() {
  const settings = await AsyncStorage.getItem('@robot_settings');
  const cfg = settings ? JSON.parse(settings) : {host: '192.168.1.100', port: 5000};
  return `http://${cfg.host}:${cfg.port}`;
}

export async function fetchStatus() {
  const base = await getBaseUrl();
  const res = await axios.get(`${base}/api/status`);
  return res.data;
}

export async function sendRobotCommand(command: string) {
  try {
    const base = await getBaseUrl();
    await axios.post(`${base}/api/command`, {command});
    return true;
  } catch (e) {
    return false;
  }
}
