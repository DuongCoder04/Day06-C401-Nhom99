export type UserContext = {
  budget: number | null
  diet: string | null
}

export type Suggestion = {
  id: string
  name: string
  price: number
  restaurant: string
  cuisine: string
  category: string
  diet_tags: string[]
  meal_tags: string[]
  is_hot: boolean
  comfort_score: number
  shareable: boolean
  popularity: number
  image_url: string
  description: string
  reason: string
  rating?: number | null
  is_open?: boolean | null
  delivery_minutes?: number | null
  delivery_fee?: number | null
  distance_km?: number | null
}

export type ChatResponse = {
  reply: string
  intent: string
  action: string
  suggestions: Suggestion[]
  cart_summary: CartResponse
  clarification_question?: string | null
}

export type MenuItem = {
  id: string
  name: string
  price: number
  restaurant: string
  cuisine: string
  category: string
  diet_tags: string[]
  meal_tags: string[]
  is_hot: boolean
  comfort_score: number
  shareable: boolean
  popularity: number
  image_url: string
  description: string
}

export type CartItem = {
  dish_id: string
  name: string
  price: number
  restaurant: string
  image_url: string
  quantity: number
}

export type CartResponse = {
  items: CartItem[]
  total: number
  item_count: number
}

export type ChatMessage = {
  id: string
  role: 'user' | 'ai'
  text: string
  suggestions?: Suggestion[]
}

export type UserPreferences = {
  budget: number
  diet: string
  note: string
}
