// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'

const isDesktopBuild: boolean = process.env.NUXT_DESKTOP_BUILD === '1'

// Dedicated build dir for `scripts/typecheck.mjs`: the running dev server owns `.nuxt`.
const typecheckBuildDirectory: string | undefined = process.env.NUXT_TYPECHECK_BUILD_DIR

export default defineNuxtConfig({
  ...(typecheckBuildDirectory ? { buildDir: typecheckBuildDirectory } : {}),

  modules: ['@nuxt/eslint', '@nuxt/ui', '@pinia/nuxt'],

  // The Tauri window loads a static generation; the web app is served with SSR.
  ssr: !isDesktopBuild,

  components: [
    { path: '~/components/ui', prefix: 'Ui' },
    { path: '~/components', pathPrefix: false, ignore: ['**/ui/**'] },
  ],

  devtools: { enabled: !isDesktopBuild },

  app: {
    head: {
      title: 'La Bonne Truffe',
      htmlAttrs: { lang: 'fr' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'Les portées de cocker spaniel anglais qui te correspondent, et une notification dès qu’une naît.',
        },
        { name: 'theme-color', content: '#FBF6EE' },
        { name: 'robots', content: 'noindex, nofollow' },
        // PWA: installable on the iPhone and iPad home screen, the only way iOS delivers Web Push.
        { name: 'mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'default' },
        { name: 'apple-mobile-web-app-title', content: 'Bonne Truffe' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32x32.png' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
        { rel: 'manifest', href: '/site.webmanifest' },
      ],
    },
  },

  css: ['~/assets/css/main.css'],

  ui: {
    // Fredoka and Nunito are self-hosted through @fontsource (see main.css), not by @nuxt/fonts.
    fonts: false,
    // A single light theme: the validated mockup has no dark variant.
    colorMode: false,
    theme: {
      colors: ['primary', 'neutral', 'success', 'warning', 'error'],
    },
  },

  icon: {
    // Bundle the Lucide icons the app uses, so the offline Tauri window never fetches them.
    clientBundle: { scan: true },
  },

  runtimeConfig: {
    public: {
      // The production domain is not chosen yet (docs/08): set NUXT_PUBLIC_API_BASE when building for the VPS.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      // True for the Tauri build: no Web Push there, the iPhone and iPad receive the notifications.
      isDesktop: isDesktopBuild,
    },
  },

  compatibilityDate: '2026-10-01',

  nitro: isDesktopBuild ? { preset: 'static' } : undefined,

  typescript: {
    strict: true,
    typeCheck: false,
  },

  eslint: {
    config: {
      stylistic: false,
    },
  },
})
