import { useCallback, useEffect, useRef, useState } from 'react'
import { getMenu } from '../lib/api'
import type { MenuItem } from '../types/api'

export type MenuFilters = {
  q: string
  budget: number | null
  diet: string
}

const initialFilters: MenuFilters = {
  q: '',
  budget: null,
  diet: '',
}

function applyFilters(items: MenuItem[], filters: MenuFilters): MenuItem[] {
  return items.filter((item) => {
    const matchesQuery =
      !filters.q ||
      [item.name, item.restaurant, item.description, item.cuisine, item.category]
        .join(' ')
        .toLowerCase()
        .includes(filters.q.toLowerCase())

    const matchesBudget = !filters.budget || item.price <= filters.budget
    const matchesDiet = !filters.diet || item.diet_tags.includes(filters.diet)

    return matchesQuery && matchesBudget && matchesDiet
  })
}

export function useMenu(defaultFilters?: Partial<MenuFilters>) {
  const allItemsRef = useRef<MenuItem[]>([])
  const [items, setItems] = useState<MenuItem[]>([])
  const [filters, setFilters] = useState<MenuFilters>({ ...initialFilters, ...defaultFilters })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Use a ref for filters inside the async load to avoid stale closure
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  const load = useCallback(async (nextFilters?: Partial<MenuFilters>) => {
    setLoading(true)
    setError(null)

    try {
      // Merge passed overrides with current filters (via ref, not closure)
      const merged: MenuFilters = { ...filtersRef.current, ...nextFilters }
      setFilters(merged)
      filtersRef.current = merged

      // Fetch only on first load; reuse cache afterwards
      if (!allItemsRef.current.length) {
        const fetched = await getMenu()
        allItemsRef.current = fetched
      }

      setItems(applyFilters(allItemsRef.current, merged))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tải được menu')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, []) // stable — no deps needed because we use refs

  // Initial load
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load(defaultFilters)
    }, 0)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { items, filters, loading, error, load, setFilters }
}
