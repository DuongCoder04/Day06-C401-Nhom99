import { API_BASE_URL } from './config'
import type {
  CartResponse,
  ChatResponse,
  MenuItem,
  UserContext,
} from '../types/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data && typeof data.detail === 'string' ? data.detail : `API error ${response.status}`
    throw new Error(detail)
  }

  return data as T
}

export function getMenu() {
  return request<MenuItem[]>('/menu')
}

export type BackendConfig = {
  llm_enabled: boolean
  mode: string
  weather_enabled: boolean
  web_search_enabled: boolean
}

export function getConfig() {
  return request<BackendConfig>('/config')
}

export function sendChat(payload: { message: string; sessionId: string; userContext: UserContext }) {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: payload.message,
      session_id: payload.sessionId,
      user_context: payload.userContext,
    }),
  })
}

export function getCart(sessionId: string) {
  return request<CartResponse>(`/cart/${sessionId}`)
}

export function addToCart(sessionId: string, dishId: string, quantity = 1) {
  return request<CartResponse>('/cart/add', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, dish_id: dishId, quantity }),
  })
}

export function removeFromCart(sessionId: string, dishId: string) {
  return request<CartResponse>('/cart/remove', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, dish_id: dishId }),
  })
}
