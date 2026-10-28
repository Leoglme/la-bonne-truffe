/** One entry of the tab bar (iPad, iPhone) and of the sidebar (desktop). */
export type MainNavigationEntry = {
  label: string
  path: string
  icon: string
}

/** The four tabs of the mockup: Portées (patte), Suivi (cœur), Critères (curseurs), Réglages (engrenage). */
export const MAIN_NAVIGATION_ENTRIES: readonly MainNavigationEntry[] = [
  { label: 'Portées', path: '/', icon: 'i-lucide-paw-print' },
  { label: 'Suivi', path: '/suivi', icon: 'i-lucide-heart' },
  { label: 'Critères', path: '/criteres', icon: 'i-lucide-sliders-horizontal' },
  { label: 'Réglages', path: '/reglages', icon: 'i-lucide-settings' },
]
