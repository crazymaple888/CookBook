import { Ionicons } from '@expo/vector-icons';
import { Link } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  FlatList,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { useMatch } from '@/features/home/queries';
import { useIngredientCategories } from '@/features/match/queries';
import type { Ingredient } from '@/lib/types';

export default function MatchScreen() {
  const { data: categories } = useIngredientCategories();
  const [selected, setSelected] = useState<Map<number, Ingredient>>(new Map());
  const [freeText, setFreeText] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const toggle = (ing: Ingredient) => {
    setSubmitted(false);
    setSelected((prev) => {
      const next = new Map(prev);
      if (next.has(ing.id)) next.delete(ing.id);
      else next.set(ing.id, ing);
      return next;
    });
  };

  const addFreeText = () => {
    const t = input.trim();
    if (!t) return;
    setSubmitted(false);
    setFreeText((prev) => (prev.includes(t) ? prev : [...prev, t]));
    setInput('');
  };

  const query = useMatch(
    submitted ? [...selected.keys()] : [],
    submitted ? freeText : [],
  );

  const results = query.data;
  const selectedList = useMemo(() => [...selected.values()], [selected]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>我有什么食材？</Text>
      <Text style={styles.subtitle}>点选或输入你现有的食材，看看能做什么菜</Text>

      {/* Selected chips */}
      {(selectedList.length > 0 || freeText.length > 0) && (
        <View style={styles.chips}>
          {selectedList.map((ing) => (
            <TouchableOpacity key={ing.id} style={styles.chip} onPress={() => toggle(ing)}>
              <Text style={styles.chipText}>{ing.name}</Text>
              <Ionicons name="close" size={14} color="#6fae97" />
            </TouchableOpacity>
          ))}
          {freeText.map((t) => (
            <TouchableOpacity
              key={t}
              style={styles.chip}
              onPress={() => {
                setFreeText((prev) => prev.filter((x) => x !== t));
                setSubmitted(false);
              }}>
              <Text style={styles.chipText}>{t}</Text>
              <Ionicons name="close" size={14} color="#6fae97" />
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Free text input */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          placeholder="输入食材，如：番茄"
          placeholderTextColor="#aab3ac"
          value={input}
          onChangeText={setInput}
          onSubmitEditing={addFreeText}
          returnKeyType="done"
        />
        <TouchableOpacity style={styles.addBtn} onPress={addFreeText}>
          <Ionicons name="add" size={20} color="#e8ece8" />
        </TouchableOpacity>
      </View>

      {/* Match button */}
      <TouchableOpacity
        style={[
          styles.matchBtn,
          (selectedList.length === 0 && freeText.length === 0) || submitted ? styles.matchBtnDisabled : null,
        ]}
        disabled={selectedList.length === 0 && freeText.length === 0}
        onPress={() => setSubmitted(true)}>
        <Ionicons name="search" size={18} color="#e8ece8" />
        <Text style={styles.matchBtnText}>
          {submitted ? '重新匹配' : '开始匹配菜谱'}
        </Text>
      </TouchableOpacity>

      {/* Results */}
      {submitted && query.isLoading && <Text style={styles.loading}>匹配中…</Text>}
      {submitted && results && (
        <View style={styles.results}>
          <Text style={styles.resultsHeader}>
            共找到 {results.total} 道菜
            {results.unresolved_names.length > 0
              ? `，无法识别：${results.unresolved_names.join('、')}`
              : ''}
          </Text>
          {results.items.map((item, i) => (
            <ResultCard key={item.recipe.id} item={item} index={i} />
          ))}
          {results.items.length === 0 && (
            <Text style={styles.empty}>没有匹配到菜谱，试试增加食材</Text>
          )}
        </View>
      )}

      {/* Category picker */}
      <Text style={styles.sectionTitle}>从分类中选择</Text>
      {categories?.map((cat) => (
        <View key={cat.id} style={styles.category}>
          <Text style={styles.categoryName}>{cat.name}</Text>
          <View style={styles.ingGrid}>
            {cat.ingredients.map((ing) => {
              const isSel = selected.has(ing.id);
              return (
                <TouchableOpacity
                  key={ing.id}
                  style={[styles.ingChip, isSel && styles.ingChipSel]}
                  onPress={() => toggle(ing)}>
                  <Text style={[styles.ingText, isSel && styles.ingTextSel]}>{ing.name}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

function ResultCard({ item, index }: { item: any; index: number }) {
  const matched = item.matched_ingredients.length;
  const missing = item.missing_ingredients.length;
  const pct = Math.round(item.coverage * 100);
  return (
    <Link href={`/recipe/${item.recipe.id}`} asChild>
      <View style={styles.resultCard}>
        <View style={styles.resultHeader}>
          <Text style={styles.resultTitle}>{item.recipe.title}</Text>
          <View style={[styles.coverage, item.is_complete ? styles.coverageFull : null]}>
            <Text style={styles.coverageText}>{item.is_complete ? '食材齐全' : `${pct}%`}</Text>
          </View>
        </View>
        <Text style={styles.resultMeta}>
          已匹配 {matched} 种 · 还缺 {missing} 种
        </Text>
        {item.missing_ingredients.length > 0 && (
          <View style={styles.missingRow}>
            <Text style={styles.missingLabel}>需购买：</Text>
            {item.missing_ingredients.map((m: any, i: number) => (
              <Text key={i} style={styles.missingItem}>
                {m.name}
                {m.raw_text ? `(${m.raw_text})` : ''}
              </Text>
            ))}
          </View>
        )}
      </View>
    </Link>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'transparent' },
  content: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: '800', color: '#e8ece8' },
  subtitle: { fontSize: 14, color: '#aab3ac', marginTop: 4, marginBottom: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#232926',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  chipText: { color: '#6fae97', fontWeight: '600' },
  inputRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  input: {
    flex: 1,
    backgroundColor: '#1c211e',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#3a403c',
    color: '#e8ece8',
  },
  addBtn: {
    width: 46,
    borderRadius: 12,
    backgroundColor: '#2f5d50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  matchBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#2f5d50',
    borderRadius: 14,
    paddingVertical: 14,
    marginBottom: 20,
  },
  matchBtnDisabled: { opacity: 0.5 },
  matchBtnText: { color: '#e8ece8', fontSize: 16, fontWeight: '700' },
  loading: { color: '#aab3ac', textAlign: 'center', marginVertical: 20 },
  results: { marginBottom: 20 },
  resultsHeader: { fontSize: 15, fontWeight: '700', color: '#e8ece8', marginBottom: 10 },
  resultCard: {
    width: '100%',
    backgroundColor: '#1c211e',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  resultTitle: { fontSize: 16, fontWeight: '700', color: '#e8ece8', flex: 1 },
  coverage: { backgroundColor: '#2a3430', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3 },
  coverageFull: { backgroundColor: '#2f5d50' },
  coverageText: { color: '#c7cfc9', fontWeight: '700', fontSize: 12 },
  resultMeta: { fontSize: 13, color: '#aab3ac', marginTop: 6 },
  missingRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  missingLabel: { fontSize: 13, color: '#d99a26', fontWeight: '600' },
  missingItem: { fontSize: 13, color: '#b3761c' },
  empty: { color: '#aab3ac', textAlign: 'center', marginVertical: 20 },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: '#e8ece8', marginBottom: 12, marginTop: 8 },
  category: { marginBottom: 16 },
  categoryName: { fontSize: 15, fontWeight: '600', color: '#c7cfc9', marginBottom: 8 },
  ingGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  ingChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1c211e',
    borderWidth: 1,
    borderColor: '#3a403c',
  },
  ingChipSel: { backgroundColor: '#2f5d50', borderColor: '#2f5d50' },
  ingText: { color: '#c7cfc9' },
  ingTextSel: { color: '#e8ece8', fontWeight: '600' },
});
