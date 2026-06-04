import type { ChatMessage } from '../../types/api'
import { MessageBubble } from './MessageBubble'

export function MessageList({
  messages,
  onAddToCart,
}: {
  messages: ChatMessage[]
  onAddToCart?: (id: string) => void
}) {
  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onAddToCart={onAddToCart} />
      ))}
    </div>
  )
}
