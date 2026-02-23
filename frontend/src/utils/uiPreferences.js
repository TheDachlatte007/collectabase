const STORAGE_KEY = 'collectabase_ui_prefs'

const THEME_OPTIONS = ['indigo', 'emerald', 'sunset']
const DENSITY_OPTIONS = ['comfortable', 'compact']

export function defaultUiPrefs() {
  return {
    theme: 'indigo',
    density: 'comfortable'
  }
}

export function loadUiPrefs() {
  const defaults = defaultUiPrefs()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaults
    const parsed = JSON.parse(raw)
    const theme = THEME_OPTIONS.includes(parsed?.theme) ? parsed.theme : defaults.theme
    const density = DENSITY_OPTIONS.includes(parsed?.density) ? parsed.density : defaults.density
    return { theme, density }
  } catch {
    return defaults
  }
}

export function applyUiPrefs(prefs) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.setAttribute('data-theme', prefs.theme)
  root.setAttribute('data-density', prefs.density)
}

export function saveUiPrefs(prefs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
}

export function setUiPrefs(next) {
  const prefs = {
    ...defaultUiPrefs(),
    ...next
  }
  applyUiPrefs(prefs)
  saveUiPrefs(prefs)
  return prefs
}
