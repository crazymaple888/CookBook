import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { Ingredient, IngredientCategory } from '@/lib/types';

export function useIngredientCategories() {
  return useQuery({
    queryKey: ['ingredient-categories'],
    queryFn: () => api.get<IngredientCategory[]>('/ingredients/categories'),
  });
}

export function useIngredientSearch(q: string) {
  return useQuery({
    queryKey: ['ingredient-search', q],
    queryFn: () => api.get<{ items: Ingredient[] }>(`/ingredients/search?q=${encodeURIComponent(q)}`),
    enabled: q.trim().length > 0,
  });
}
