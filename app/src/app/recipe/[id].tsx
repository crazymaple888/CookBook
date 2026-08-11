import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useNavigation, useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { categoryEmoji } from '@/components/recipe-card';
import { useFavorite, useRecipeDetail, useToggleLike, useUnfavorite } from '@/features/home/queries';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';
import { useQueryClient } from '@tanstack/react-query';

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const recipeId = Number(id);
  const router = useRouter();
  const navigation = useNavigation();
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const { data: recipe, isLoading } = useRecipeDetail(recipeId);
  const favorite = useFavorite(recipeId);
  const unfavorite = useUnfavorite(recipeId);
  const like = useToggleLike(recipeId);
  const [commentText, setCommentText] = useState('');

  if (isLoading || !recipe) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#e6532e" />
      </View>
    );
  }

  const toggleFavorite = () => {
    if (!user) {
      router.push('/auth');
      return;
    }
    if (recipe.is_favorited) unfavorite.mutate();
    else favorite.mutate();
  };

  const toggleLike = () => {
    if (!user) {
      router.push('/auth');
      return;
    }
    like.mutate();
  };

  const submitComment = async () => {
    if (!commentText.trim()) return;
    if (!user) {
      router.push('/auth');
      return;
    }
    await api.post(`/recipes/${recipeId}/comments`, { content: commentText.trim() });
    setCommentText('');
    qc.invalidateQueries({ queryKey: ['comments', recipeId] });
    qc.invalidateQueries({ queryKey: ['recipe', recipeId] });
  };

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
          <Ionicons name="chevron-back" size={24} color="#1f1f1f" />
        </TouchableOpacity>
        <Text style={styles.topTitle}>菜谱详情</Text>
        <View style={styles.topRight} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {recipe.cover_url ? (
          <Image source={{ uri: recipe.cover_url }} style={styles.cover} resizeMode="cover" />
        ) : (
          <View style={[styles.cover, styles.placeholderCover]}>
            <Text style={styles.placeholderEmoji}>{categoryEmoji(recipe.title)}</Text>
          </View>
        )}

        <View style={styles.body}>
          <Text style={styles.title}>{recipe.title}</Text>
          {recipe.description ? <Text style={styles.desc}>{recipe.description}</Text> : null}

          <View style={styles.statsRow}>
            <Stat icon="heart" value={recipe.likes_count} />
            <Stat icon="bookmark" value={recipe.favorites_count} />
            <Stat icon="chatbubble" value={recipe.comments_count} />
          </View>

          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.actionBtn, recipe.is_liked && styles.actionActive]}
              onPress={toggleLike}>
              <Ionicons name={recipe.is_liked ? 'heart' : 'heart-outline'} size={20} color={recipe.is_liked ? '#d9574a' : '#555'} />
              <Text style={styles.actionText}>点赞</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, recipe.is_favorited && styles.actionActive]}
              onPress={toggleFavorite}>
              <Ionicons name={recipe.is_favorited ? 'bookmark' : 'bookmark-outline'} size={20} color={recipe.is_favorited ? '#e0a437' : '#555'} />
              <Text style={styles.actionText}>{recipe.is_favorited ? '已收藏' : '收藏'}</Text>
            </TouchableOpacity>
          </View>

          {/* Ingredients */}
          <SectionTitle>食材</SectionTitle>
          {recipe.ingredients.length > 0 ? (
            recipe.ingredients.map((ing) => (
              <View key={ing.id} style={styles.ingRow}>
                <Text style={styles.ingName}>{ing.name}</Text>
                <Text style={styles.ingQty}>{ing.raw_text || [ing.quantity, ing.unit].filter(Boolean).join(' ')}</Text>
              </View>
            ))
          ) : (
            <Text style={styles.emptyHint}>暂无食材信息</Text>
          )}

          {/* Steps */}
          <SectionTitle>步骤</SectionTitle>
          {recipe.steps.length > 0 ? (
            recipe.steps.map((s, i) => (
              <View key={i} style={styles.stepRow}>
                <View style={styles.stepNum}>
                  <Text style={styles.stepNumText}>{i + 1}</Text>
                </View>
                <Text style={styles.stepText}>{s.text}</Text>
              </View>
            ))
          ) : (
            <Text style={styles.emptyHint}>暂无步骤</Text>
          )}

          {/* Comments */}
          <SectionTitle>评论</SectionTitle>
          {user ? (
            <View style={styles.commentInputRow}>
              <TextInput
                style={styles.commentInput}
                placeholder="说点什么…"
                value={commentText}
                onChangeText={setCommentText}
              />
              <TouchableOpacity style={styles.commentBtn} onPress={submitComment}>
                <Text style={styles.commentBtnText}>发送</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity onPress={() => router.push('/auth')}>
              <Text style={styles.loginHint}>登录后可以评论</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

function Stat({ icon, value }: { icon: any; value: number }) {
  return (
    <View style={styles.stat}>
      <Ionicons name={icon} size={16} color="#8a8a8a" />
      <Text style={styles.statText}>{value}</Text>
    </View>
  );
}

function SectionTitle({ children }: { children: string }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7f6f3' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f7f6f3' },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#f7f6f3',
  },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  topTitle: { fontSize: 17, fontWeight: '700', color: '#1f1f1f' },
  topRight: { width: 40 },
  content: { paddingBottom: 40 },
  cover: { width: '100%', height: 220, backgroundColor: '#e8e6e8' },
  placeholderCover: { alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 80 },
  body: { padding: 18 },
  title: { fontSize: 24, fontWeight: '800', color: '#1f1f1f' },
  desc: { fontSize: 14, color: '#666', marginTop: 6, lineHeight: 20 },
  statsRow: { flexDirection: 'row', gap: 18, marginTop: 14 },
  stat: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  statText: { fontSize: 14, color: '#555' },
  actions: { flexDirection: 'row', gap: 12, marginTop: 16 },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5e3e5',
  },
  actionActive: { backgroundColor: '#fdeee8', borderColor: '#f5c2b0' },
  actionText: { color: '#555', fontWeight: '600' },
  sectionTitle: { fontSize: 18, fontWeight: '800', color: '#1f1f1f', marginTop: 26, marginBottom: 12 },
  ingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 9,
    borderBottomWidth: 1,
    borderBottomColor: '#efedef',
  },
  ingName: { fontSize: 15, color: '#333' },
  ingQty: { fontSize: 14, color: '#888' },
  stepRow: { flexDirection: 'row', gap: 12, marginBottom: 14 },
  stepNum: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#e6532e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  stepText: { flex: 1, fontSize: 15, color: '#333', lineHeight: 22 },
  commentInputRow: { flexDirection: 'row', gap: 8 },
  commentInput: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderWidth: 1,
    borderColor: '#e5e3e5',
  },
  commentBtn: {
    backgroundColor: '#e6532e',
    borderRadius: 12,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  commentBtnText: { color: '#fff', fontWeight: '700' },
  loginHint: { color: '#e6532e', fontSize: 14 },
  emptyHint: { color: '#999' },
});
