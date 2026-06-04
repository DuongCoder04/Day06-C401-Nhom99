import type { ChatMessage, Suggestion } from '../../types/api'

function SuggestionCard({
  suggestion,
  onAdd,
}: {
  suggestion: Suggestion
  onAdd?: (id: string) => void
}) {
  return (
    <div className="suggestion-card">
      <img
        src={suggestion.image_url || 'https://placehold.co/90x78?text=Yumi'}
        alt={suggestion.name}
      />
      <div className="suggestion-body">
        <strong>{suggestion.name}</strong>
        <span>{suggestion.restaurant}</span>
        <span>{new Intl.NumberFormat('vi-VN').format(suggestion.price)}đ</span>
        {suggestion.reason ? (
          <span className="suggestion-reason">{suggestion.reason}</span>
        ) : null}
        {onAdd ? (
          <button
            type="button"
            className="suggestion-add-btn"
            onClick={() => onAdd(suggestion.id)}
          >
            + Thêm vào giỏ
          </button>
        ) : null}
      </div>
    </div>
  )
}

function parseMessageContent(text: string) {
  if (!text) return null

  const lines = text.split('\n')

  return lines.map((line, lineIndex) => {
    // Helper to format inline bold text (**bold**)
    const formatInline = (str: string) => {
      if (!str) return ''
      const parts = str.split(/(\*\*.*?\*\*)/g)
      return parts.map((part, partIndex) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={partIndex} className="ai-highlight">
              {part.slice(2, -2)}
            </strong>
          )
        }
        return part
      })
    }

    const trimmed = line.trim()

    // Check if empty line (for paragraph spacing)
    if (!trimmed) {
      return <div key={lineIndex} className="ai-paragraph-spacing" />
    }

    // Check for headings: e.g. "### " or "#### "
    if (trimmed.startsWith('### ') || trimmed.startsWith('#### ')) {
      const headingText = trimmed.replace(/^#+\s+/, '')
      return (
        <h4 key={lineIndex} className="ai-heading">
          {formatInline(headingText)}
        </h4>
      )
    }

    // Check for bullet lists starting with "- " or "* "
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const rawText = trimmed.substring(2)
      return (
        <div key={lineIndex} className="ai-list-item">
          <span className="ai-list-bullet">•</span>
          <span className="ai-list-text">{formatInline(rawText)}</span>
        </div>
      )
    }

    // Check for numbered lists starting with "1. ", "2. ", etc.
    const numMatch = trimmed.match(/^(\d+)\.\s(.*)/)
    if (numMatch) {
      const num = numMatch[1]
      const rawText = numMatch[2]
      return (
        <div key={lineIndex} className="ai-list-item">
          <span className="ai-list-num">{num}.</span>
          <span className="ai-list-text">{formatInline(rawText)}</span>
        </div>
      )
    }

    // Regular line, format inline and wrap in a paragraph div
    return (
      <div key={lineIndex} className="ai-paragraph">
        {formatInline(line)}
      </div>
    )
  })
}

export function MessageBubble({
  message,
  onAddToCart,
}: {
  message: ChatMessage
  onAddToCart?: (id: string) => void
}) {
  const isAssistant = message.role === 'ai'

  return (
    <article className={`message ${message.role}`}>
      {isAssistant ? (
        <div className="message-avatar assistant-avatar" title="Yumi Agent">
          🍲
        </div>
      ) : null}

      <div className="bubble-wrapper">
        <div className="bubble-sender">
          {isAssistant ? 'Yumi Agent' : 'Bạn'}
        </div>
        <div className="bubble">
          <div className="bubble-content">{parseMessageContent(message.text)}</div>
          {message.suggestions?.length ? (
            <div className="suggestion-list">
              {message.suggestions.slice(0, 3).map((suggestion) => (
                <SuggestionCard
                  key={suggestion.id}
                  suggestion={suggestion}
                  onAdd={onAddToCart}
                />
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {!isAssistant ? (
        <div className="message-avatar user-avatar" title="Bạn">
          👤
        </div>
      ) : null}
    </article>
  )
}
