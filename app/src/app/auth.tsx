import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { ApiError } from '@/lib/api';
import { useAuthStore } from '@/store/auth';

export default function AuthScreen() {
  const { login, register } = useAuthStore();
  const router = useRouter();
  const navigation = useNavigation();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [account, setAccount] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(account, password);
      } else {
        await register(username, password, email || undefined);
      }
      if (navigation.canGoBack()) {
        router.back();
      } else {
        router.replace('/');
      }
    } catch (e) {
      Alert.alert('提示', e instanceof ApiError ? e.message : '操作失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => {
            if (navigation.canGoBack()) {
              router.back();
            } else {
              router.replace('/');
            }
          }}>
          <Ionicons name="close" size={22} color="#1f1f1f" />
        </TouchableOpacity>
      </View>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>{mode === 'login' ? '欢迎回来' : '创建账号'}</Text>
        <Text style={styles.subtitle}>
          {mode === 'login' ? '登录后可以收藏和点赞菜谱' : '注册即可收藏、发布菜谱'}
        </Text>

        {mode === 'register' && (
          <TextInput
            style={styles.input}
            placeholder="用户名"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        )}
        <TextInput
          style={styles.input}
          placeholder={mode === 'login' ? '用户名或邮箱' : '邮箱（可选）'}
          value={mode === 'login' ? account : email}
          onChangeText={mode === 'login' ? setAccount : setEmail}
          keyboardType={mode === 'register' ? 'email-address' : 'default'}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="密码"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity style={[styles.authBtn, busy && styles.disabled]} onPress={submit} disabled={busy}>
          <Text style={styles.authBtnText}>{busy ? '处理中…' : mode === 'login' ? '登录' : '注册'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'register' : 'login')}>
          <Text style={styles.switch}>
            {mode === 'login' ? '还没有账号？去注册' : '已有账号？去登录'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7f6f3' },
  topBar: { paddingHorizontal: 12, paddingTop: 12 },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  content: { padding: 28, paddingTop: 30 },
  title: { fontSize: 28, fontWeight: '800', color: '#1f1f1f' },
  subtitle: { fontSize: 14, color: '#8a8a8a', marginTop: 4, marginBottom: 28 },
  input: {
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#e5e3e5',
    marginBottom: 12,
  },
  authBtn: {
    backgroundColor: '#e6532e',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  authBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  disabled: { opacity: 0.5 },
  switch: { color: '#e6532e', textAlign: 'center', marginTop: 18, fontSize: 14 },
});
