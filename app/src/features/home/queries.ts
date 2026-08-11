import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { MatchResponse, Page, RecipeCard, RecipeDetail } from '@/lib/types';

export function useRandomRecipes(count = 10) {
  return useQuery({
    queryKey: ['recipes', 'random', count],
    queryFn: () => api.get<RecipeCard[]>(`/recipes/random?count=${count}`),
  });
}

export function useRecipeDetail(id: number) {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: () => api.get<RecipeDetail>(`/recipes/${id}`),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useRecipes(params: {
  query?: string;
  categoryId?: number;
  sort?: 'new' | 'hot';
  page?: number;
  pageSize?: number;
}) {
  const qs = new URLSearchParams();
  if (params.query) qs.set('query', params.query);
  if (params.categoryId) qs.set('category_id', String(params.categoryId));
  qs.set('sort', params.sort ?? 'new');
  qs.set('page', String(params.page ?? 1));
  qs.set('page_size', String(params.pageSize ?? 20));
  return useQuery({
    queryKey: ['recipes', params.query ?? '', params.categoryId ?? '', params.sort ?? 'new', params.page ?? 1],
    queryFn: () => api.get<Page<RecipeCard>>(`/recipes?${qs.toString()}`),
  });
}

export function useFavorite(recipeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ status: string }>(`/recipes/${recipeId}/favorite`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recipe', recipeId] });
      qc.invalidateQueries({ queryKey: ['favorites'] });
    },
  });
}

export function useUnfavorite(recipeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<undefined>(`/recipes/${recipeId}/favorite`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recipe', recipeId] });
      qc.invalidateQueries({ queryKey: ['favorites'] });
    },
  });
}

export function useToggleLike(recipeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ liked: boolean; likes_count: number }>(`/recipes/${recipeId}/like`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recipe', recipeId] });
    },
  });
}

export function useMyFavorites(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['favorites', page],
    queryFn: () => api.get<Page<RecipeCard>>(`/users/me/favorites?page=${page}&page_size=${pageSize}`),
  });
}

export function useMyRecipes(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['my-recipes', page],
    queryFn: () => api.get<Page<RecipeCard>>(`/recipes/users/me/recipes?page=${page}&page_size=${pageSize}`),
  });
}

export function useMatch(ingredientIds: number[], ingredientNames: string[]) {
  return useQuery({
    queryKey: ['match', ingredientIds.join(','), ingredientNames.join(',')],
    queryFn: () =>
      api.post<MatchResponse>('/match', {
        ingredient_ids: ingredientIds,
        ingredient_names: ingredientNames,
        page: 1,
        page_size: 20,
      }),
    enabled: ingredientIds.length > 0 || ingredientNames.length > 0,
  });
}
