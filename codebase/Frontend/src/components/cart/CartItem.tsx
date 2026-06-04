import type { CartItem as CartItemType } from '../../types/api'
import { Button } from '../ui/Button'

export function CartItem({ item, onRemove }: { item: CartItemType; onRemove: (id: string) => void }) {
  return (
    <article className="cart-item">
      <div style={{ minWidth: 0, flex: 1 }}>
        <strong>{item.name}</strong>
        <small>
          {new Intl.NumberFormat('vi-VN').format(item.price)}đ &nbsp;×&nbsp; {item.quantity}
          &ensp;=&nbsp;
          <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>
            {new Intl.NumberFormat('vi-VN').format(item.price * item.quantity)}đ
          </span>
        </small>
        <small style={{ color: 'var(--muted)' }}>{item.restaurant}</small>
      </div>
      <Button
        type="button"
        className="ghost"
        style={{ minHeight: 30, padding: '0 10px', fontSize: 12, flexShrink: 0 }}
        onClick={() => onRemove(item.dish_id)}
        aria-label={`Xóa ${item.name}`}
      >
        ✕
      </Button>
    </article>
  )
}
