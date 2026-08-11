import { Ionicons } from '@expo/vector-icons';
import { Link } from 'expo-router';
import { Image, StyleSheet, Text, View } from 'react-native';

import type { RecipeCard as RecipeCardType } from '@/lib/types';

const EMOJI_BY_TITLE: [RegExp, string][] = [
  [/蛋|番茄|西红柿/, '🍳'],
  [/鸡|鸭|鹅/, '🍗'],
  [/鱼|虾|蟹|海鲜|虾仁/, '🦐'],
  [/猪|肉|牛|羊|排骨|五花/, '🥩'],
  [/蔬菜|白菜|菠菜|青菜/, '🥬'],
  [/汤/, '🍲'],
  [/粥/, '🥣'],
  [/面|粉/, '🍜'],
  [/饭/, '🍚'],
  [/豆腐|豆/, '🫘'],
  [/蛋糕|甜品|甜点/, '🍰'],
  [/饼/, '🫓'],
  [/沙拉|凉拌/, '🥗'],
];

const CARD_COLORS = ['#fdeee8', '#e8f4ec', '#e8effb', '#faf0e4', '#f0e9fb', '#e9f7f5'];

export function categoryEmoji(title: string, fallback = '🍽️'): string {
  for (const [re, emoji] of EMOJI_BY_TITLE) {
    if (re.test(title)) return emoji;
  }
  return fallback;
}

export function RecipeCard({ recipe, index = 0 }: { recipe: RecipeCardType; index?: number }) {
  const bg = CARD_COLORS[index % CARD_COLORS.length];
  return (
    <Link href={`/recipe/${recipe.id}`} asChild>
      <View style={styles.card}>
        {recipe.cover_url ? (
          <Image
            source={{ uri: recipe.cover_url }}
            style={styles.cover}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.cover, { backgroundColor: bg, alignItems: 'center', justifyContent: 'center' }]}>
            <Text style={styles.placeholderEmoji}>{categoryEmoji(recipe.title)}</Text>
          </View>
        )}
        <View style={styles.body}>
          <Text style={styles.title} numberOfLines={1}>
            {recipe.title}
          </Text>
          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="heart" size={13} color="#d9574a" />
              <Text style={styles.metaText}>{recipe.likes_count}</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="bookmark" size={13} color="#e0a437" />
              <Text style={styles.metaText}>{recipe.favorites_count}</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="chatbubble" size={13} color="#5b7fd4" />
              <Text style={styles.metaText}>{recipe.comments_count}</Text>
            </View>
          </View>
        </View>
      </View>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#f0eef0',
    marginBottom: 16,
  },
  cover: {
    width: '100%',
    height: 160,
    backgroundColor: '#f0eef0',
  },
  placeholderEmoji: {
    fontSize: 56,
  },
  body: {
    padding: 14,
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1f1f1f',
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 14,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 13,
    color: '#777',
  },
});
