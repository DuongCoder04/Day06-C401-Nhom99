import type { CartResponse } from '../../types/api'
import { CartItem } from './CartItem'
import { CartSummary } from './CartSummary'
import { EmptyState } from '../ui/EmptyState'
import { Button } from '../ui/Button'

export function CartPanel({
  cart,
  onRemove,
  onCheckout,
}: {
  cart: CartResponse
  onRemove: (id: string) => void
  onCheckout: () => void
}) {
  const itemCount = cart.item_count

  return (
    <section className="cart-window">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Checkout preview</p>
          <h2>Giỏ hàng</h2>
        </div>
      </header>

      <CartSummary total={cart.total} itemCount={itemCount} />

      <div className="cart-list">
        {!cart.items.length ? (
          <EmptyState>Chọn món từ card gợi ý hoặc menu bên trái để thêm vào giỏ.</EmptyState>
        ) : (
          cart.items.map((item) => <CartItem key={item.dish_id} item={item} onRemove={onRemove} />)
        )}
      </div>

      <div className="cart-footer">
        <span>Demo checkout</span>
        <strong>Không thanh toán thật</strong>
        <Button type="button" disabled={!itemCount} onClick={onCheckout}>Đặt hàng demo</Button>
      </div>
    </section>
  )
}
