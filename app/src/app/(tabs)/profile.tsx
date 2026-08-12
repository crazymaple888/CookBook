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
import { useApplyUpload, useUploadStatus } from '@/features/upload/queries';

export default function ProfileScreen() {
  const { user, hydrated, login, register, logout } = useAuthStore();
  const router = useRouter();
  const { data: uploadStatus, isLoading: statusLoading } = useUploadStatus(user?.id);
  const applyUpload = useApplyUpload();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [notice, setNotice] = useState('');
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
    const isAdmin = user.is_admin;
    const status = isAdmin ? 'approved' : (uploadStatus?.status ?? 'none');

    const showNotice = (text: string) => {
      setNotice(text);
      setTimeout(() => setNotice(''), 3000);
    };

    const handlePublishPress = () => {
      if (isAdmin || status === 'approved') {
        router.push('/recipe/create');
      } else if (status === 'pending') {
        showNotice('你的上传权限申请正在审核中，请耐心等待');
      } else {
        // none or rejected -> apply directly
        applyUpload.mutate(undefined, {
          onSuccess: () => showNotice('申请已提交，等待管理员审核'),
          onError: () => showNotice('申请失败，请稍后重试'),
        });
      }
    };

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

        {notice ? <View style={styles.noticeBar}><Text style={styles.noticeText}>{notice}</Text></View> : null}

        <TouchableOpacity style={styles.menuItem} onPress={handlePublishPress}>
          <Ionicons name="add-circle" size={20} color="#6fae97" />
          <Text style={styles.menuText}>
            {isAdmin || status === 'approved'
              ? '发布菜谱'
              : status === 'pending'
                ? '上传权限审核中'
                : status === 'rejected'
                  ? '重新申请上传权限'
                  : '申请上传权限'}
          </Text>
          <Ionicons name="chevron-forward" size={18} color="#ccc" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/recipe/me')}>
          <Ionicons name="document-text" size={20} color="#2f5d50" />
          <Text style={styles.menuText}>我发布的菜谱</Text>
          <Ionicons name="chevron-forward" size={18} color="#ccc" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/favorites')}>
          <Ionicons name="bookmark" size={20} color="#c99a3d" />
          <Text style={styles.menuText}>我的收藏</Text>
          <Ionicons name="chevron-forward" size={18} color="#ccc" />
        </TouchableOpacity>

        {isAdmin && (
          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/admin')}>
            <Ionicons name="shield-checkmark" size={20} color="#6fae97" />
            <Text style={styles.menuText}>审核上传申请</Text>
            <Ionicons name="chevron-forward" size={18} color="#ccc" />
          </TouchableOpacity>
        )}

        <TouchableOpacity style={[styles.menuItem, styles.logout]} onPress={logout}>
          <Ionicons name="log-out" size={20} color="#c96f5a" />
          <Text style={[styles.menuText, { color: '#c96f5a' }]}>退出登录</Text>
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
            placeholderTextColor="#aab3ac"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        )}
        <TextInput
          style={styles.input}
          placeholder={mode === 'login' ? '用户名或邮箱' : '邮箱（可选）'}
          placeholderTextColor="#aab3ac"
          value={mode === 'login' ? account : email}
          onChangeText={mode === 'login' ? setAccount : setEmail}
          keyboardType={mode === 'register' ? 'email-address' : 'default'}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="密码"
          placeholderTextColor="#aab3ac"
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
  container: { flex: 1, backgroundColor: 'transparent' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: 'transparent' },
  content: { padding: 20 },
  noticeBar: {
    backgroundColor: '#2a3430',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  noticeText: { color: '#c7cfc9', fontSize: 14, textAlign: 'center' },
  avatarWrap: { alignItems: 'center', marginVertical: 24 },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#2f5d50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 32, color: '#e8ece8', fontWeight: '700' },
  name: { fontSize: 20, fontWeight: '700', marginTop: 10, color: '#e8ece8' },
  username: { fontSize: 14, color: '#aab3ac', marginTop: 2 },
  bio: { fontSize: 14, color: '#c7cfc9', marginTop: 8, textAlign: 'center' },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1c211e',
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  menuText: { flex: 1, fontSize: 16, color: '#e8ece8' },
  logout: { marginTop: 20 },
  authContent: { padding: 28, paddingTop: 60 },
  authTitle: { fontSize: 28, fontWeight: '800', color: '#e8ece8' },
  authSubtitle: { fontSize: 14, color: '#aab3ac', marginTop: 4, marginBottom: 28 },
  input: {
    backgroundColor: '#1c211e',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#3a403c',
    color: '#e8ece8',
    marginBottom: 12,
  },
  authBtn: {
    backgroundColor: '#2f5d50',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  authBtnText: { color: '#e8ece8', fontSize: 16, fontWeight: '700' },
  disabled: { opacity: 0.5 },
  switch: { color: '#2f5d50', textAlign: 'center', marginTop: 18, fontSize: 14 },
});
