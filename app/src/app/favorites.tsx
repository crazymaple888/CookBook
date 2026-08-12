import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRouter } from 'expo-router';
import { FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { RecipeCard } from '@/components/recipe-card';
import { useMyFavorites } from '@/features/home/queries';

export default function FavoritesScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const { data, isLoading } = useMyFavorites();

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
        <Text style={styles.topTitle}>我的收藏</Text>
        <View style={styles.topRight} />
      </View>
      <FlatList
        data={data?.items ?? []}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item, index }) => <RecipeCard recipe={item} index={index} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>{isLoading ? '加载中…' : '还没有收藏任何菜谱'}</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'transparent' },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#1c211e', alignItems: 'center', justifyContent: 'center' },
  topTitle: { fontSize: 17, fontWeight: '700', color: '#e8ece8' },
  topRight: { width: 40 },
  list: { padding: 16 },
  empty: { color: '#aab3ac', textAlign: 'center', marginTop: 40 },
});
