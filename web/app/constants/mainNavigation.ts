import type { MainNavigationEntry, PushedScreenBackLabel } from '~/types/MainNavigation'

/** From this width, a detail spreads over two columns and a choice opens in a window. */
export const WIDE_SCREEN_MEDIA_QUERY: string = '(min-width: 1280px)'

/** Checked before the entries of the navigation, whose paths these screens start with. */
export const PUSHED_SCREEN_BACK_LABELS: PushedScreenBackLabel[] = [
  { pathPattern: /^\/portees\/\d+/, label: 'La portée' },
  { pathPattern: /^\/eleveurs\/recherche/, label: 'Recherche' },
  { pathPattern: /^\/eleveurs\/\d+/, label: 'L’élevage' },
  { pathPattern: /^\/notifications/, label: 'Notifications' },
  { pathPattern: /^\/carte/, label: 'Carte' },
]

export const MAIN_NAVIGATION_ENTRIES: MainNavigationEntry[] = [
  { label: 'Portées', path: '/', icon: 'paw', activeIcon: 'paw-filled', isInTabBar: true },
  { label: 'Suivi', path: '/suivi', icon: 'heart', activeIcon: 'heart-filled', isInTabBar: true },
  { label: 'Éleveurs', path: '/eleveurs', icon: 'house', activeIcon: 'house-filled', isInTabBar: true },
  { label: 'Critères', path: '/criteres', icon: 'sliders', activeIcon: 'sliders', isInTabBar: true },
  { label: 'Sources', path: '/sources', icon: 'rss', activeIcon: 'rss', isInTabBar: false },
  { label: 'Réglages', path: '/reglages', icon: 'gear', activeIcon: 'gear', isInTabBar: true },
]
