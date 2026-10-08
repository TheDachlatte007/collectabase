import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const appShell = await readFile(new URL('../src/App.vue', import.meta.url), 'utf8')

test('desktop sidebar navigation icons have an explicit fixed size', () => {
  assert.match(
    appShell,
    /\.nav-icon\s*\{[\s\S]*?width:\s*1\.5rem;[\s\S]*?height:\s*1\.5rem;/,
  )
})
