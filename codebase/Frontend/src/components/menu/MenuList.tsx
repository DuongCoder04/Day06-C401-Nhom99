import type { MenuItem } from '../../types/api'
import { MenuCard } from './MenuCard'
import { EmptyState } from '../ui/EmptyState'

export function MenuList({ items, onAdd }: { items: MenuItem[]; onAdd: (id: string) => void }) {
  if (!items.length) {
    return <EmptyState>Không tìm thấy món phù hợp.</EmptyState>
  }

  return (
    <div className="menu-list">
      {items.map((item) => (
        <MenuCard key={item.id} item={item} onAdd={onAdd} />
      ))}
    </div>
  )
}
