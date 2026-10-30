import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: { '~': fileURLToPath(new URL('./app', import.meta.url)) },
  },
  test: {
    include: ['tests/**/*.test.ts'],
    // The smoke test builds the whole Nuxt app once before rendering it.
    hookTimeout: 240_000,
    testTimeout: 60_000,
  },
})
