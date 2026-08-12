import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { ApiError, api } from '@/lib/api';

type IngredientRow = { name: string; quantity: string; unit: string };
type StepRow = { text: string };

export default function CreateRecipeScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [prepTime, setPrepTime] = useState('');
  const [cookTime, setCookTime] = useState('');
  const [ingredients, setIngredients] = useState<IngredientRow[]>([{ name: '', quantity: '', unit: '' }]);
  const [steps, setSteps] = useState<StepRow[]>([{ text: '' }]);
  const [submitting, setSubmitting] = useState(false);

  const updateIngredient = (index: number, field: keyof IngredientRow, value: string) => {
    setIngredients((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)),
    );
  };

  const updateStep = (index: number, value: string) => {
    setSteps((prev) => prev.map((row, i) => (i === index ? { text: value } : row)));
  };

  const submit = async () => {
    if (!title.trim()) {
      Alert.alert('提示', '请输入菜谱标题');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || null,
        cover_url: coverUrl.trim() || null,
        prep_time: prepTime ? Number(prepTime) : null,
        cook_time: cookTime ? Number(cookTime) : null,
        steps: steps
          .map((s, i) => ({ step: i + 1, text: s.text.trim() }))
          .filter((s) => s.text),
        ingredients: ingredients
          .filter((ing) => ing.name.trim())
          .map((ing) => ({
            name: ing.name.trim(),
            quantity: ing.quantity ? Number(ing.quantity) : null,
            unit: ing.unit.trim() || null,
          })),
      };
      const created = await api.post<{ id: number }>('/recipes', payload);
      Alert.alert('发布成功', '你的菜谱已发布', [
        {
          text: '查看',
          onPress: () => router.replace(`/recipe/${created.id}`),
        },
        { text: '好的', onPress: () => router.back() },
      ]);
    } catch (e) {
      Alert.alert('发布失败', e instanceof ApiError ? e.message : '请稍后重试');
    } finally {
      setSubmitting(false);
    }
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
          <Ionicons name="chevron-back" size={24} color="#e8ece8" />
        </TouchableOpacity>
        <Text style={styles.topTitle}>发布菜谱</Text>
        <View style={styles.topRight} />
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.label}>标题 *</Text>
        <TextInput
          style={styles.input}
          placeholder="菜谱名称，如：番茄炒蛋"
          placeholderTextColor="#aab3ac"
          value={title}
          onChangeText={setTitle}
        />

        <Text style={styles.label}>描述</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="介绍一下这道菜…"
          placeholderTextColor="#aab3ac"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={3}
        />

        <Text style={styles.label}>封面图片 URL（可选）</Text>
        <TextInput
          style={styles.input}
          placeholder="https://…"
          placeholderTextColor="#aab3ac"
          value={coverUrl}
          onChangeText={setCoverUrl}
          autoCapitalize="none"
        />

        <View style={styles.row}>
          <View style={styles.rowItem}>
            <Text style={styles.label}>准备（分钟）</Text>
            <TextInput
              style={styles.input}
              placeholder="如：10"
              placeholderTextColor="#aab3ac"
              value={prepTime}
              onChangeText={setPrepTime}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.rowItem}>
            <Text style={styles.label}>烹饪（分钟）</Text>
            <TextInput
              style={styles.input}
              placeholder="如：15"
              placeholderTextColor="#aab3ac"
              value={cookTime}
              onChangeText={setCookTime}
              keyboardType="numeric"
            />
          </View>
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>食材</Text>
          <TouchableOpacity
            onPress={() => setIngredients((prev) => [...prev, { name: '', quantity: '', unit: '' }])}>
            <Ionicons name="add-circle" size={24} color="#6fae97" />
          </TouchableOpacity>
        </View>
        {ingredients.map((ing, i) => (
          <View key={i} style={styles.ingRow}>
            <TextInput
              style={[styles.input, styles.ingName]}
              placeholder="食材名"
              placeholderTextColor="#aab3ac"
              value={ing.name}
              onChangeText={(v) => updateIngredient(i, 'name', v)}
            />
            <TextInput
              style={[styles.input, styles.ingQty]}
              placeholder="用量"
              placeholderTextColor="#aab3ac"
              value={ing.quantity}
              onChangeText={(v) => updateIngredient(i, 'quantity', v)}
              keyboardType="numeric"
            />
            <TextInput
              style={[styles.input, styles.ingUnit]}
              placeholder="单位"
              placeholderTextColor="#aab3ac"
              value={ing.unit}
              onChangeText={(v) => updateIngredient(i, 'unit', v)}
            />
            {ingredients.length > 1 && (
              <TouchableOpacity
                onPress={() => setIngredients((prev) => prev.filter((_, idx) => idx !== i))}>
                <Ionicons name="close-circle" size={20} color="#c96f5a" />
              </TouchableOpacity>
            )}
          </View>
        ))}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>步骤</Text>
          <TouchableOpacity onPress={() => setSteps((prev) => [...prev, { text: '' }])}>
            <Ionicons name="add-circle" size={24} color="#6fae97" />
          </TouchableOpacity>
        </View>
        {steps.map((step, i) => (
          <View key={i} style={styles.stepRow}>
            <View style={styles.stepNum}>
              <Text style={styles.stepNumText}>{i + 1}</Text>
            </View>
            <TextInput
              style={[styles.input, styles.stepInput]}
              placeholder="这一步怎么做…"
              placeholderTextColor="#aab3ac"
              value={step.text}
              onChangeText={(v) => updateStep(i, v)}
              multiline
            />
            {steps.length > 1 && (
              <TouchableOpacity
                onPress={() => setSteps((prev) => prev.filter((_, idx) => idx !== i))}>
                <Ionicons name="close-circle" size={20} color="#c96f5a" />
              </TouchableOpacity>
            )}
          </View>
        ))}

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={submit}
          disabled={submitting}>
          <Text style={styles.submitBtnText}>{submitting ? '发布中…' : '发布菜谱'}</Text>
        </TouchableOpacity>
      </ScrollView>
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
    backgroundColor: 'transparent',
  },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#1c211e', alignItems: 'center', justifyContent: 'center' },
  topTitle: { fontSize: 17, fontWeight: '700', color: '#e8ece8' },
  topRight: { width: 40 },
  content: { padding: 16, paddingBottom: 40 },
  label: { fontSize: 14, color: '#aab3ac', marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: '#1c211e',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#3a403c',
    color: '#e8ece8',
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  row: { flexDirection: 'row', gap: 12 },
  rowItem: { flex: 1 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 20, marginBottom: 10 },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: '#e8ece8' },
  ingRow: { flexDirection: 'row', gap: 8, alignItems: 'center', marginBottom: 8 },
  ingName: { flex: 1 },
  ingQty: { width: 60 },
  ingUnit: { width: 60 },
  stepRow: { flexDirection: 'row', gap: 8, alignItems: 'center', marginBottom: 8 },
  stepNum: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#2f5d50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumText: { color: '#e8ece8', fontWeight: '700', fontSize: 13 },
  stepInput: { flex: 1 },
  submitBtn: {
    backgroundColor: '#2f5d50',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 24,
  },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: { color: '#e8ece8', fontSize: 16, fontWeight: '700' },
});
