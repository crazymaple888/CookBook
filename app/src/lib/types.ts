export type User = {
  id: number;
  username: string;
  email: string | null;
  nickname: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_admin: boolean;
  created_at: string;
};

export type RecipeCard = {
  id: number;
  title: string;
  description: string | null;
  cover_url: string | null;
  category_id: number | null;
  likes_count: number;
  favorites_count: number;
  comments_count: number;
};

export type RecipeIngredientOut = {
  id: number;
  name: string;
  raw_text: string | null;
  quantity: number | null;
  unit: string | null;
  is_main: boolean;
};

export type RecipeDetail = RecipeCard & {
  steps: { step: number; text: string; image_url?: string | null }[];
  prep_time: number | null;
  cook_time: number | null;
  servings: number | null;
  difficulty: string | null;
  created_at: string;
  is_favorited: boolean;
  is_liked: boolean;
  ingredients: RecipeIngredientOut[];
};

export type Ingredient = {
  id: number;
  name: string;
  category_id: number | null;
  image_url: string | null;
};

export type IngredientCategory = {
  id: number;
  name: string;
  sort_order: number;
  ingredients: Ingredient[];
};

export type MatchIngredient = {
  name: string;
  raw_text: string | null;
  quantity: number | null;
  unit: string | null;
  label: string | null;
};

export type MatchResultItem = {
  recipe: RecipeCard;
  coverage: number;
  is_complete: boolean;
  matched_ingredients: MatchIngredient[];
  missing_ingredients: MatchIngredient[];
};

export type MatchResponse = {
  items: MatchResultItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  unresolved_names: string[];
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
};

export type Comment = {
  id: number;
  recipe_id: number;
  user_id: number;
  parent_id: number | null;
  content: string;
  created_at: string;
  author_name: string | null;
  replies: Comment[];
};
