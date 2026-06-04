import type { InputHTMLAttributes } from 'react'

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`yumi-input ${props.className ?? ''}`.trim()} />
}
