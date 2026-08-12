import { Ionicons } from '@expo/vector-icons';
import { useCallback, useMemo } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { RecipeCard } from '@/components/recipe-card';
import { useRandomRecipesInfinite } from '@/features/home/queries';
import type { RecipeCard as RecipeCardType } from '@/lib/types';

export default function HomeScreen() {
  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
    isRefetching,
  } = useRandomRecipesInfinite();

  // Flatten pages and dedup by recipe id (random API may repeat across pages).
  const recipes = useMemo(() => {
    const seen = new Set<number>();
    const result: RecipeCardType[] = [];
    for (const page of data?.pages ?? []) {
      for (const r of page) {
        if (!seen.has(r.id)) {
          seen.add(r.id);
          result.push(r);
        }
      }
    }
    return result;
  }, [data]);

  const loadMore = useCallback(() => {
    if (!isFetchingNextPage && hasNextPage) {
      fetchNextPage();
    }
  }, [isFetchingNextPage, hasNextPage, fetchNextPage]);

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      data={recipes}
      keyExtractor={(item) => String(item.id)}
      renderItem={({ item, index }) => <RecipeCard recipe={item} index={index} />}
      refreshControl={
        <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#2f5d50" />
      }
      onEndReached={loadMore}
      onEndReachedThreshold={0.3}
      ListHeaderComponent={
        <View style={styles.header}>
          <View style={styles.titleBlock}>
            <View style={styles.titleAccent} />
            <View>
              <Text style={styles.title}>今日灵感</Text>
              <Text style={styles.subtitle}>下拉刷新，发现新菜谱</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.refreshBtn} onPress={() => refetch()} disabled={isLoading}>
            <Ionicons name="refresh" size={22} color="#2f5d50" />
          </TouchableOpacity>
        </View>
      }
      ListEmptyComponent={
        isLoading ? (
          <Text style={styles.loading}>加载中…</Text>
        ) : (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>还没有菜谱，去后台导入数据吧</Text>
          </View>
        )
      }
      ListFooterComponent={
        isFetchingNextPage ? (
          <View style={styles.footer}>
            <ActivityIndicator color="#2f5d50" />
          </View>
        ) : null
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'transparent' },
  content: { padding: 16, paddingBottom: 32 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  titleBlock: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  titleAccent: {
    width: 4,
    height: 32,
    borderRadius: 2,
    backgroundColor: '#2f5d50',
  },
  title: { fontSize: 26, fontWeight: '800', color: '#e8ece8', letterSpacing: 0.5 },
  subtitle: { fontSize: 14, color: '#aab3ac', marginTop: 2 },
  refreshBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#1c211e',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  loading: { color: '#aab3ac', textAlign: 'center', marginTop: 40 },
  empty: { paddingVertical: 60, alignItems: 'center' },
  emptyText: { color: '#aab3ac' },
  footer: { paddingVertical: 20, alignItems: 'center' },
});
