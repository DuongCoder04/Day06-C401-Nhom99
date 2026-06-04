import type { ChatMessage } from '../../types/api'
import { ChatInput } from './ChatInput'
import { MessageList } from './MessageList'
import { QuickActions } from './QuickActions'
import { TypingIndicator } from './TypingIndicator'

export function ChatWindow({
  messages,
  loading,
  onSend,
  onQuickAction,
  onReset,
  intentLabel,
  onAddToCart,
}: {
  messages: ChatMessage[]
  loading: boolean
  onSend: (value: string) => void
  onQuickAction: (value: string) => void
  onReset: () => void
  intentLabel: string
  onAddToCart?: (id: string) => void
}) {
  // Hero collapses once the user has sent at least one message
  const hasStarted = messages.some((m) => m.role === 'user')

  return (
    <section className="chat-window">
      <header className="chat-header">
        <div>
          <p className="eyebrow">Conversational food ordering</p>
          <h1>Đặt món bằng hội thoại</h1>
        </div>
        <button type="button" className="reset-button" onClick={onReset} title="Reset chat">
          ↻
        </button>
      </header>

      <div className={`chat-hero${hasStarted ? ' chat-hero--collapsed' : ''}`}>
        <p>Yumi hiểu nhu cầu, gọi backend FastAPI và chỉ gợi ý món có thật trong menu.</p>
        <div className="hero-tags">
          <span>FastAPI backend</span>
          <span>Intent-based</span>
          <span>Cart demo</span>
        </div>
      </div>

      <QuickActions onPick={onQuickAction} />
      <p className="intent-label">{intentLabel}</p>

      <MessageList messages={messages} onAddToCart={onAddToCart} />

      {loading ? <TypingIndicator /> : null}

      <ChatInput onSend={onSend} disabled={loading} />
    </section>
  )
}
