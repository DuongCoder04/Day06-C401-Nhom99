export function MenuFilters({
  onBudget,
  onDiet,
  onReset,
}: {
  onBudget: (value: number) => void
  onDiet: (value: string) => void
  onReset: () => void
}) {
  return (
    <div className="menu-filters">
      <button type="button" onClick={() => onBudget(80000)}>Dưới 80k</button>
      <button type="button" onClick={() => onDiet('healthy')}>Healthy</button>
      <button type="button" onClick={() => onDiet('low_cal')}>Low cal</button>
      <button type="button" onClick={onReset}>Tất cả</button>
    </div>
  )
}
