import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRouter } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { useReviewUpload, useUploadRequests } from '@/features/admin/queries';
import { useAuthStore } from '@/store/auth';

export default function AdminScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const { data, isLoading } = useUploadRequests();
  const review = useReviewUpload();

  useEffect(() => {
    if (hydrated && (!user || !user.is_admin)) {
      router.replace('/');
    }
  }, [hydrated, user, router]);

  if (!hydrated) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#6fae97" />
      </View>
    );
  }

  if (!user || !user.is_admin) {
    return (
      <View style={styles.center}>
        <Ionicons name="shield-outline" size={56} color="#c96f5a" />
        <Text style={styles.noAccessText}>没有权限访问管理页面</Text>
        <TouchableOpacity style={styles.backHomeBtn} onPress={() => router.replace('/')}>
          <Text style={styles.backHomeText}>返回首页</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
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
          <Ionicons name="chevron-back" size={24} color="#e8ece8" />
        </TouchableOpacity>
        <Text style={styles.topTitle}>上传申请审核</Text>
        <View style={styles.topRight} />
      </View>

      <FlatList
        data={data ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <Text style={styles.hint}>
            {isLoading ? '加载中…' : data && data.length > 0 ? `共 ${data.length} 个待审核申请` : '当前没有待审核的申请'}
          </Text>
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{(item.nickname || item.username)[0]}</Text>
              </View>
              <View style={styles.info}>
                <Text style={styles.name}>{item.nickname || item.username}</Text>
                <Text style={styles.username}>@{item.username}</Text>
                {item.email ? <Text style={styles.email}>{item.email}</Text> : null}
              </View>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>待审核</Text>
              </View>
            </View>
            <View style={styles.actions}>
              <TouchableOpacity
                style={[styles.btn, styles.approveBtn]}
                disabled={review.isPending}
                onPress={() => review.mutate({ userId: item.id, action: 'approve' })}>
                <Text style={styles.approveText}>通过</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, styles.rejectBtn]}
                disabled={review.isPending}
                onPress={() => review.mutate({ userId: item.id, action: 'reject' })}>
                <Text style={styles.rejectText}>拒绝</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        ListEmptyComponent={
          !isLoading ? <Text style={styles.empty}>暂无待审核申请</Text> : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'transparent' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: 'transparent', padding: 24 },
  noAccessText: { color: '#e8ece8', fontSize: 16, marginTop: 16, textAlign: 'center' },
  backHomeBtn: {
    backgroundColor: '#2f5d50',
    borderRadius: 12,
    paddingHorizontal: 24,
    paddingVertical: 12,
    marginTop: 20,
  },
  backHomeText: { color: '#e8ece8', fontSize: 15, fontWeight: '700' },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: 'transparent',
  },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#1c211e', alignItems: 'center', justifyContent: 'center' },
  topTitle: { fontSize: 17, fontWeight: '700', color: '#e8ece8' },
  topRight: { width: 40 },
  list: { padding: 16 },
  hint: { fontSize: 14, color: '#aab3ac', marginBottom: 12 },
  card: {
    backgroundColor: '#1c211e',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2f5d50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 18, color: '#e8ece8', fontWeight: '700' },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: '700', color: '#e8ece8' },
  username: { fontSize: 13, color: '#aab3ac', marginTop: 1 },
  email: { fontSize: 12, color: '#aab3ac', marginTop: 1 },
  badge: { backgroundColor: '#2a3430', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText: { color: '#c7cfc9', fontSize: 12, fontWeight: '600' },
  actions: { flexDirection: 'row', gap: 10, marginTop: 14 },
  btn: { flex: 1, borderRadius: 10, paddingVertical: 10, alignItems: 'center' },
  approveBtn: { backgroundColor: '#2f5d50' },
  approveText: { color: '#e8ece8', fontWeight: '700' },
  rejectBtn: { backgroundColor: '#3a2f2c' },
  rejectText: { color: '#d9a8a0', fontWeight: '700' },
  empty: { color: '#aab3ac', textAlign: 'center', marginTop: 40 },
});
