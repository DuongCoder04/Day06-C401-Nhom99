const actions = ['Ăn gì giờ?', 'Dưới 80k', 'Đang giảm cân', 'Xem giỏ hàng']

export function QuickActions({ onPick }: { onPick: (value: string) => void }) {
  return (
    <div className="quick-actions">
      {actions.map((action) => (
        <button key={action} type="button" onClick={() => onPick(action)}>
          {action}
        </button>
      ))}
    </div>
  )
}
