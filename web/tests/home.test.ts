import { fileURLToPath } from 'node:url'
import { $fetch, setup } from '@nuxt/test-utils/e2e'
import { describe, expect, it } from 'vitest'

describe('home page', async (): Promise<void> => {
  await setup({ rootDir: fileURLToPath(new URL('..', import.meta.url)), server: true, browser: false })

  it('renders the litters screen in the validated art direction', async (): Promise<void> => {
    const html: string = await $fetch<string>('/')

    expect(html).toContain('La Bonne Truffe')
    expect(html).toContain('Les portées')
    expect(html).toContain('aria-label="Navigation principale"')
    expect(html).toContain('href="/suivi"')
  })

  it('serves the PWA manifest and the push service worker', async (): Promise<void> => {
    const manifest: { name: string; display: string } = await $fetch('/site.webmanifest', { responseType: 'json' })
    const serviceWorker: string = await $fetch<string>('/sw.js', { responseType: 'text' })

    expect(manifest.name).toBe('La Bonne Truffe')
    expect(manifest.display).toBe('standalone')
    expect(serviceWorker).toContain("addEventListener('push'")
  })
})
