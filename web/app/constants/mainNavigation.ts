import type { MainNavigationEntry } from '~/types/MainNavigation'

export const MAIN_NAVIGATION_ENTRIES: MainNavigationEntry[] = [
  { label: 'Portées', path: '/', icon: 'paw', activeIcon: 'paw-filled', isInTabBar: true },
  { label: 'Suivi', path: '/suivi', icon: 'heart', activeIcon: 'heart-filled', isInTabBar: true },
  { label: 'Critères', path: '/criteres', icon: 'sliders', activeIcon: 'sliders', isInTabBar: true },
  { label: 'Sources', path: '/sources', icon: 'rss', activeIcon: 'rss', isInTabBar: false },
  { label: 'Réglages', path: '/reglages', icon: 'gear', activeIcon: 'gear', isInTabBar: true },
]
