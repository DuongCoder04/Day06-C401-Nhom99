import type { PropsWithChildren } from 'react'

export function ErrorState({ children }: PropsWithChildren) {
  return <div className="yumi-error">{children}</div>
}
