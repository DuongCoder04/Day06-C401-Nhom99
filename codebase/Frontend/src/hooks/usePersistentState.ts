import { useEffect, useState } from 'react'

export function usePersistentState<T>(initialValue: T, read: () => T, write: (value: T) => void) {
  const [value, setValue] = useState<T>(() => {
    try {
      return read()
    } catch {
      return initialValue
    }
  })
  const [ready] = useState(true)

  useEffect(() => {
    if (!ready) return
    write(value)
  }, [ready, value, write])

  return [value, setValue, ready] as const
}
