import type { MenuItem } from '../../types/api'
import { Button } from '../ui/Button'

export function MenuCard({ item, onAdd }: { item: MenuItem; onAdd: (id: string) => void }) {
  return (
    <article className="menu-card">
      <img src={item.image_url ?? 'https://placehold.co/82x82?text=Yumi'} alt={item.name} />
      <div>
        <strong>{item.name}</strong>
        <small>{new Intl.NumberFormat('vi-VN').format(item.price)}đ · {item.restaurant}</small>
        <small>{item.description}</small>
        <Button type="button" onClick={() => onAdd(item.id)}>Thêm vào giỏ</Button>
      </div>
    </article>
  )
}
