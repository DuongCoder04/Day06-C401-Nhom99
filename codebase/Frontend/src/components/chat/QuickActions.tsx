import type { BackendConfig } from '../../lib/api'

const BASE_ACTIONS = ['Ăn gì giờ?', 'Dưới 80k', 'Đang giảm cân', 'Xem giỏ hàng']
const WEATHER_ACTIONS = ['Trời mưa ăn gì?', 'Trời lạnh ăn gì?']
const WEB_ACTIONS = ['Quán phở nào ngon?', 'Review đồ ăn healthy']
const AGENT_ACTIONS = ['Gợi ý combo', 'Cho nhóm 4 người']

export function QuickActions({
  onPick,
  config,
}: {
  onPick: (value: string) => void
  config?: BackendConfig
}) {
  const actions = [
    ...BASE_ACTIONS,
    ...(config?.weather_enabled ? WEATHER_ACTIONS : []),
    ...(config?.web_search_enabled ? WEB_ACTIONS : []),
    ...(config?.llm_enabled ? AGENT_ACTIONS : []),
  ].slice(0, 8) // cap at 8 chips

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
