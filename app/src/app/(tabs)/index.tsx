import { Ionicons } from '@expo/vector-icons';
import { RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { RecipeCard } from '@/components/recipe-card';
import { useRandomRecipes } from '@/features/home/queries';

export default function HomeScreen() {
  const { data, isLoading, isRefetching, refetch } = useRandomRecipes(10);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#e6532e" />}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>今日灵感</Text>
          <Text style={styles.subtitle}>下拉刷新，发现新菜谱</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={() => refetch()} disabled={isLoading}>
          <Ionicons name="refresh" size={22} color="#e6532e" />
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <Text style={styles.loading}>加载中…</Text>
      ) : data && data.length > 0 ? (
        data.map((r, i) => <RecipeCard key={r.id} recipe={r} index={i} />)
      ) : (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>还没有菜谱，去后台导入数据吧</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7f6f3' },
  content: { padding: 16, paddingBottom: 32 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  title: { fontSize: 26, fontWeight: '800', color: '#1f1f1f' },
  subtitle: { fontSize: 14, color: '#8a8a8a', marginTop: 2 },
  refreshBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#f0eef0',
  },
  loading: { color: '#8a8a8a', textAlign: 'center', marginTop: 40 },
  empty: { paddingVertical: 60, alignItems: 'center' },
  emptyText: { color: '#8a8a8a' },
});
