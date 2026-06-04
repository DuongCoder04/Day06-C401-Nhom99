import { useEffect, useState } from 'react'
import { getConfig, type BackendConfig } from '../lib/api'

const DEFAULT_CONFIG: BackendConfig = {
  llm_enabled: false,
  mode: 'rule_based_fallback',
  weather_enabled: false,
  web_search_enabled: false,
}

export function useConfig() {
  const [config, setConfig] = useState<BackendConfig>(DEFAULT_CONFIG)

  useEffect(() => {
    getConfig()
      .then(setConfig)
      .catch(() => setConfig(DEFAULT_CONFIG))
  }, [])

  return config
}
