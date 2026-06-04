import { useCallback, useMemo, useState } from 'react'
import { sendChat } from '../lib/api'
import type { CartResponse, ChatMessage, ChatResponse, UserContext } from '../types/api'

function makeMessage(role: 'user' | 'ai', text: string, suggestions: ChatMessage['suggestions'] = []) {
  return {
    id: crypto.randomUUID(),
    role,
    text,
    suggestions,
  } satisfies ChatMessage
}

function formatAssistantReply(result: ChatResponse) {
  if (result.clarification_question) {
    return `${result.reply}\n\n${result.clarification_question}`
  }

  return result.reply
}

export function useChat(sessionId: string, userContext: UserContext) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    makeMessage('ai', 'Chào bạn, mình là Yumi. Bạn có thể nhắn “Ăn gì giờ?”, “Có gì dưới 80k?” hoặc “Tôi đang giảm cân” để mình gợi ý món phù hợp.'),
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [intentLabel, setIntentLabel] = useState('Yumi đang sẵn sàng')
  const [cartSummary, setCartSummary] = useState<CartResponse>({ items: [], total: 0, item_count: 0 })

  const sendMessage = useCallback(async (text: string) => {
    const message = text.trim()
    if (!message) return null

    setMessages((current) => [...current, makeMessage('user', message)])
    setLoading(true)
    setError(null)
    setIntentLabel('Yumi đang suy nghĩ...')

    try {
      const result = await sendChat({ message, sessionId, userContext })
      setMessages((current) => [...current, makeMessage('ai', formatAssistantReply(result), result.suggestions)])
      setIntentLabel(`Intent: ${result.intent} · Action: ${result.action}`)
      setCartSummary(result.cart_summary)
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Không gửi được tin nhắn'
      setError(errorMessage)
      setMessages((current) => [...current, makeMessage('ai', `Mình chưa kết nối được backend hoặc có lỗi: ${errorMessage}. Bạn thử lại nhé.`)])
      setIntentLabel('Backend offline')
      return null
    } finally {
      setLoading(false)
    }
  }, [sessionId, userContext])

  const resetChat = useCallback(() => {
    setMessages([
      makeMessage('ai', 'Chào bạn, mình là Yumi. Bạn có thể nhắn “Ăn gì giờ?”, “Có gì dưới 80k?” hoặc “Tôi đang giảm cân” để mình gợi ý món phù hợp.'),
    ])
    setError(null)
    setIntentLabel('Yumi đang sẵn sàng')
    setCartSummary({ items: [], total: 0, item_count: 0 })
  }, [])

  return useMemo(() => ({
    messages,
    loading,
    error,
    intentLabel,
    cartSummary,
    sendMessage,
    resetChat,
  }), [messages, loading, error, intentLabel, cartSummary, sendMessage, resetChat])
}
