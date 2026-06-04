export function CartSummary({ total, itemCount }: { total: number; itemCount: number }) {
  return (
    <div className="cart-summary">
      <span>{itemCount} món đã chọn</span>
      <strong>{new Intl.NumberFormat('vi-VN').format(total)}đ</strong>
    </div>
  )
}
