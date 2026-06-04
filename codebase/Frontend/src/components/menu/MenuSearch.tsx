import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function MenuSearch({
  value,
  onChange,
  onSubmit,
}: {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
}) {
  return (
    <form
      className="menu-search"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <Input value={value} onChange={(event) => onChange(event.target.value)} placeholder="Tìm món hoặc quán..." />
      <Button type="submit">Tìm</Button>
    </form>
  )
}
