const STORAGE_KEY = 'collectabase_ui_prefs'

const THEME_OPTIONS = ['indigo', 'emerald', 'sunset', 'ocean', 'rose', 'slate']
const DENSITY_OPTIONS = ['comfortable', 'compact']

export function defaultUiPrefs() {
  return {
    theme: 'indigo',
    density: 'comfortable'
  }
}

function normalizeUiPrefs(prefs) {
  const defaults = defaultUiPrefs()
  return {
    theme: THEME_OPTIONS.includes(prefs?.theme) ? prefs.theme : defaults.theme,
    density: DENSITY_OPTIONS.includes(prefs?.density) ? prefs.density : defaults.density,
  }
}

export function loadUiPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultUiPrefs()
    return normalizeUiPrefs(JSON.parse(raw))
  } catch {
    return defaultUiPrefs()
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
  const prefs = normalizeUiPrefs(next)
  applyUiPrefs(prefs)
  saveUiPrefs(prefs)
  return prefs
}
