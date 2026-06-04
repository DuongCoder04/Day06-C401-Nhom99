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

export function MessageBubble({
  message,
  onAddToCart,
}: {
  message: ChatMessage
  onAddToCart?: (id: string) => void
}) {
  return (
    <article className={`message ${message.role}`}>
      <div className="bubble">
        <p style={{ whiteSpace: 'pre-line' }}>{message.text}</p>
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
    </article>
  )
}
