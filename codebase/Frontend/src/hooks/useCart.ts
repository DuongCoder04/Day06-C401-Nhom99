import { useCallback, useEffect, useState } from 'react'
import { addToCart, getCart, removeFromCart } from '../lib/api'
import type { CartResponse } from '../types/api'

const emptyCart: CartResponse = { items: [], total: 0, item_count: 0 }

export function useCart(sessionId: string) {
  const [cart, setCart] = useState<CartResponse>(emptyCart)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshCart = useCallback(async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)
    try {
      const next = await getCart(sessionId)
      setCart(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tải được giỏ hàng')
      setCart(emptyCart)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  const addItem = useCallback(async (dishId: string) => {
    const next = await addToCart(sessionId, dishId, 1)
    setCart(next)
  }, [sessionId])

  const removeItem = useCallback(async (dishId: string) => {
    const next = await removeFromCart(sessionId, dishId)
    setCart(next)
  }, [sessionId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshCart()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [refreshCart])

  return { cart, loading, error, refreshCart, addItem, removeItem, setCart }
}
