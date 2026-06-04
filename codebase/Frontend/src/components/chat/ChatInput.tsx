import { useState } from 'react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function ChatInput({ onSend, disabled }: { onSend: (value: string) => void; disabled?: boolean }) {
  const [value, setValue] = useState('')

  return (
    <form
      className="chat-input"
      onSubmit={(event) => {
        event.preventDefault()
        onSend(value)
        setValue('')
      }}
    >
      <Input value={value} onChange={(event) => setValue(event.target.value)} placeholder="Nhắn Yumi..." />
      <Button type="submit" disabled={disabled}>Gửi</Button>
    </form>
  )
}
