import { useCallback, useMemo, useState } from 'react'
import { useChat } from './useChat'
import { useCart } from './useCart'
import { useMenu } from './useMenu'
import {
  getSessionId,
  getStoredPreferences,
  isOnboardingDone,
  setOnboardingDone,
  setStoredPreferences,
} from '../lib/session'
import type { UserPreferences } from '../types/api'

export function useAppState() {
  const [sessionId] = useState<string>(() => getSessionId())
  const [preferences, setPreferences] = useState<UserPreferences>(() => getStoredPreferences())
  const [onboardingOpen, setOnboardingOpen] = useState(() => !isOnboardingDone())

  const userContext = useMemo(
    () => ({ budget: preferences.budget, diet: preferences.diet || null }),
    [preferences],
  )

  const chat = useChat(sessionId, userContext)
  const cart = useCart(sessionId)
  const menu = useMenu({ budget: preferences.budget, diet: preferences.diet })

  // Shared handler: send chat message and sync cart from response
  const sendChatMessage = useCallback(
    async (text: string) => {
      const result = await chat.sendMessage(text)
      if (result) cart.setCart(result.cart_summary)
    },
    [chat, cart],
  )

  // Add to cart from suggestion card in chat bubble
  const addToCartFromChat = useCallback(
    async (dishId: string) => {
      await cart.addItem(dishId)
    },
    [cart],
  )

  const savePreferences = useCallback(
    (value: { budget: number; diet: string; note: string }) => {
      const next = { ...value, note: value.note ?? '' }
      setPreferences(next)
      setStoredPreferences(next)
      setOnboardingDone(true)
      setOnboardingOpen(false)
      void menu.load({ budget: next.budget, diet: next.diet })
    },
    [menu],
  )

  const skipOnboarding = useCallback(() => {
    setOnboardingDone(true)
    setOnboardingOpen(false)
  }, [])

  return {
    sessionId,
    preferences,
    onboardingOpen,
    chat,
    cart,
    menu,
    sendChatMessage,
    addToCartFromChat,
    savePreferences,
    skipOnboarding,
  }
}
