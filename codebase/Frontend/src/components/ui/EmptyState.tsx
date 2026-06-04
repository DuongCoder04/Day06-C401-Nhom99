import type { PropsWithChildren } from 'react'

export function EmptyState({ children }: PropsWithChildren) {
  return <div className="yumi-empty">{children}</div>
}
