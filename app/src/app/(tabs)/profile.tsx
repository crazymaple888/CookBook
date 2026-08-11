import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
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

import { useAuthStore } from '@/store/auth';
import { ApiError } from '@/lib/api';

export default function ProfileScreen() {
  const { user, hydrated, login, register, logout } = useAuthStore();
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [account, setAccount] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);

  if (!hydrated) {
    return <View style={styles.center}><Text>加载中…</Text></View>;
  }

  const submit = async () => {
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(account, password);
      } else {
        await register(username, password, email || undefined);
      }
      setPassword('');
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : '操作失败';
      Alert.alert('提示', msg);
    } finally {
      setBusy(false);
    }
  };

  if (user) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.avatarWrap}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user.nickname?.[0] ?? user.username[0]}</Text>
          </View>
          <Text style={styles.name}>{user.nickname || user.username}</Text>
          <Text style={styles.username}>@{user.username}</Text>
          {user.bio ? <Text style={styles.bio}>{user.bio}</Text> : null}
        </View>

        <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/recipe/me')}>
          <Ionicons name="document-text" size={20} color="#e6532e" />
          <Text style={styles.menuText}>我发布的菜谱</Text>
          <Ionicons name="chevron-forward" size={18} color="#ccc" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/favorites')}>
          <Ionicons name="bookmark" size={20} color="#e0a437" />
          <Text style={styles.menuText}>我的收藏</Text>
          <Ionicons name="chevron-forward" size={18} color="#ccc" />
        </TouchableOpacity>

        <TouchableOpacity style={[styles.menuItem, styles.logout]} onPress={logout}>
          <Ionicons name="log-out" size={20} color="#d9574a" />
          <Text style={[styles.menuText, { color: '#d9574a' }]}>退出登录</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.authContent} keyboardShouldPersistTaps="handled">
        <Text style={styles.authTitle}>{mode === 'login' ? '欢迎回来' : '创建账号'}</Text>
        <Text style={styles.authSubtitle}>
          {mode === 'login' ? '登录后可以收藏菜谱' : '注册即可收藏、发布菜谱'}
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

        <TouchableOpacity
          style={[styles.authBtn, busy && styles.disabled]}
          onPress={submit}
          disabled={busy}>
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
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f7f6f3' },
  content: { padding: 20 },
  avatarWrap: { alignItems: 'center', marginVertical: 24 },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#e6532e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 32, color: '#fff', fontWeight: '700' },
  name: { fontSize: 20, fontWeight: '700', marginTop: 10, color: '#1f1f1f' },
  username: { fontSize: 14, color: '#8a8a8a', marginTop: 2 },
  bio: { fontSize: 14, color: '#555', marginTop: 8, textAlign: 'center' },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#f0eef0',
  },
  menuText: { flex: 1, fontSize: 16, color: '#333' },
  logout: { marginTop: 20 },
  authContent: { padding: 28, paddingTop: 60 },
  authTitle: { fontSize: 28, fontWeight: '800', color: '#1f1f1f' },
  authSubtitle: { fontSize: 14, color: '#8a8a8a', marginTop: 4, marginBottom: 28 },
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
