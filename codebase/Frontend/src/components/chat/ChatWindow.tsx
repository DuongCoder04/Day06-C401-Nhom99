import type { ChatMessage } from '../../types/api'
import type { BackendConfig } from '../../lib/api'
import { ChatInput } from './ChatInput'
import { MessageList } from './MessageList'
import { QuickActions } from './QuickActions'
import { TypingIndicator } from './TypingIndicator'

function AgentBadges({ config }: { config: BackendConfig }) {
  return (
    <div className="hero-tags">
      <span className={config.llm_enabled ? 'badge badge--green' : 'badge badge--muted'}>
        {config.llm_enabled ? '🤖 AI Agent' : '⚙️ Rule-based'}
      </span>
      {config.weather_enabled && (
        <span className="badge badge--blue">🌤 Weather</span>
      )}
      {config.web_search_enabled && (
        <span className="badge badge--orange">🔍 Web Search</span>
      )}
      <span className="badge">FastAPI</span>
      <span className="badge">SQLite</span>
    </div>
  )
}

export function ChatWindow({
  messages,
  loading,
  onSend,
  onQuickAction,
  onReset,
  intentLabel,
  onAddToCart,
  config,
}: {
  messages: ChatMessage[]
  loading: boolean
  onSend: (value: string) => void
  onQuickAction: (value: string) => void
  onReset: () => void
  intentLabel: string
  onAddToCart?: (id: string) => void
  config: BackendConfig
}) {
  const hasStarted = messages.some((m) => m.role === 'user')

  return (
    <section className="chat-window">
      <header className="chat-header">
        <div>
          <p className="eyebrow">AI Food Ordering Agent</p>
          <h1>Đặt món bằng hội thoại</h1>
        </div>
        <button type="button" className="reset-button" onClick={onReset} title="Reset chat">
          ↻
        </button>
      </header>

      <div className={`chat-hero${hasStarted ? ' chat-hero--collapsed' : ''}`}>
        <p>
          {config.llm_enabled
            ? 'Yumi dùng LLM để hiểu ngôn ngữ tự nhiên, gọi tools thực tế và sinh reply tự nhiên.'
            : 'Yumi dùng rule-based classifier. Thêm API key để kích hoạt AI Agent mode.'}
        </p>
        <AgentBadges config={config} />
      </div>

      <QuickActions onPick={onQuickAction} config={config} />
      <p className="intent-label">{intentLabel}</p>

      <MessageList messages={messages} onAddToCart={onAddToCart} />

      {loading ? <TypingIndicator /> : null}

      <ChatInput onSend={onSend} disabled={loading} />
    </section>
  )
}
