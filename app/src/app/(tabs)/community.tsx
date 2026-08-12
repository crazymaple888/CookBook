import { Ionicons } from '@expo/vector-icons';
import { useMemo, useState } from 'react';
import { FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { RecipeCard } from '@/components/recipe-card';
import { useRecipes } from '@/features/home/queries';
import type { RecipeCard as RecipeCardType } from '@/lib/types';

export default function CommunityScreen() {
  const [sort, setSort] = useState<'new' | 'hot'>('new');
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [page, setPage] = useState(1);

  const onSearch = () => setDebouncedQ(q);
  const { data } = useRecipes({ query: debouncedQ, sort, page, pageSize: 20 });

  const items: RecipeCardType[] = useMemo(() => data?.items ?? [], [data]);

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="搜索菜谱…"
          placeholderTextColor="#aab3ac"
          value={q}
          onChangeText={setQ}
          onSubmitEditing={onSearch}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.searchBtn} onPress={onSearch}>
          <Ionicons name="search" size={20} color="#e8ece8" />
        </TouchableOpacity>
      </View>

      <View style={styles.sortRow}>
        <TouchableOpacity onPress={() => setSort('new')}>
          <Text style={[styles.sortText, sort === 'new' && styles.sortActive]}>最新</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setSort('hot')}>
          <Text style={[styles.sortText, sort === 'hot' && styles.sortActive]}>最热</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item, index }) => <RecipeCard recipe={item} index={index} />}
        contentContainerStyle={styles.list}
        style={styles.listContainer}
        onEndReached={() => {
          if (data?.has_more) setPage((p) => p + 1);
        }}
        onEndReachedThreshold={0.5}
        ListEmptyComponent={<Text style={styles.empty}>暂无菜谱</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'transparent' },
  listContainer: { flex: 1, width: '100%' },
  searchRow: { flexDirection: 'row', gap: 8, padding: 16, paddingBottom: 8 },
  searchInput: {
    flex: 1,
    backgroundColor: '#1c211e',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#3a403c',
    color: '#e8ece8',
  },
  searchBtn: {
    width: 46,
    borderRadius: 12,
    backgroundColor: '#2f5d50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sortRow: { flexDirection: 'row', gap: 20, paddingHorizontal: 18, paddingBottom: 8 },
  sortText: { fontSize: 15, color: '#aab3ac', fontWeight: '600' },
  sortActive: { color: '#2f5d50', fontWeight: '800' },
  list: { padding: 16, paddingTop: 4 },
  empty: { color: '#aab3ac', textAlign: 'center', marginTop: 40 },
});
