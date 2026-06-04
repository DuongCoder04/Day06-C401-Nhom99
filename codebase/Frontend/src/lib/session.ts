const SESSION_KEY = 'yumi_session_id'
const PREF_KEY = 'yumi_preferences'
const ONBOARDING_KEY = 'yumi_onboarding_done'

export const DEFAULT_PREFERENCES = {
  budget: 80000,
  diet: '',
  note: '',
}

export function getSessionId() {
  const current = localStorage.getItem(SESSION_KEY)
  if (current) return current

  const next = crypto.randomUUID()
  localStorage.setItem(SESSION_KEY, next)
  return next
}

export function getStoredPreferences() {
  try {
    const raw = localStorage.getItem(PREF_KEY)
    if (!raw) return DEFAULT_PREFERENCES
    return { ...DEFAULT_PREFERENCES, ...JSON.parse(raw) }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

export function setStoredPreferences(value: typeof DEFAULT_PREFERENCES) {
  localStorage.setItem(PREF_KEY, JSON.stringify(value))
}

export function isOnboardingDone() {
  return localStorage.getItem(ONBOARDING_KEY) === 'true'
}

export function setOnboardingDone(value: boolean) {
  localStorage.setItem(ONBOARDING_KEY, String(value))
}
