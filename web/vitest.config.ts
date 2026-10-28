import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    // The smoke test builds the whole Nuxt app once before rendering it.
    hookTimeout: 240_000,
    testTimeout: 60_000,
  },
})
