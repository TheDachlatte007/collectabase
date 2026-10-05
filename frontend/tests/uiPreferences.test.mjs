import assert from 'node:assert/strict'
import test from 'node:test'

const storage = new Map()
globalThis.localStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
}

const attributes = new Map()
globalThis.document = {
  documentElement: {
    setAttribute: (name, value) => attributes.set(name, value),
  },
}

const { setUiPrefs } = await import('../src/utils/uiPreferences.js')

test('setUiPrefs falls back to supported theme and density values', () => {
  const prefs = setUiPrefs({ theme: 'unsupported', density: 'dense' })

  assert.deepEqual(prefs, { theme: 'indigo', density: 'comfortable' })
  assert.equal(attributes.get('data-theme'), 'indigo')
  assert.equal(attributes.get('data-density'), 'comfortable')
})
