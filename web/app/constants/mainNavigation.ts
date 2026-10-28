import type { MockupIconName } from '~/constants/mockupIcons'

/** One entry of the tab bar (iPad, iPhone) and of the sidebar (desktop). */
export type MainNavigationEntry = {
  label: string
  path: string
  icon: MockupIconName
  activeIcon: MockupIconName
  isInTabBar: boolean
}

/**
 * The tabs of the mockup: Portées (patte), Suivi (cœur), Critères (curseurs), Réglages (engrenage).
 * The desktop sidebar adds Sources (design/mockup/Desktop.dc.html) and keeps Réglages last.
 */
export const MAIN_NAVIGATION_ENTRIES: readonly MainNavigationEntry[] = [
  { label: 'Portées', path: '/', icon: 'paw', activeIcon: 'paw-filled', isInTabBar: true },
  { label: 'Suivi', path: '/suivi', icon: 'heart', activeIcon: 'heart-filled', isInTabBar: true },
  { label: 'Critères', path: '/criteres', icon: 'sliders', activeIcon: 'sliders', isInTabBar: true },
  { label: 'Sources', path: '/sources', icon: 'rss', activeIcon: 'rss', isInTabBar: false },
  { label: 'Réglages', path: '/reglages', icon: 'gear', activeIcon: 'gear', isInTabBar: true },
]

/**
 * Whether an entry leads to the current screen or to one of its sub-screens.
 *
 * @param entry - The entry.
 * @param currentPath - Path of the current route.
 * @returns True for the active entry.
 */
export function isNavigationEntryActive(entry: MainNavigationEntry, currentPath: string): boolean {
  if (entry.path === '/') {
    return currentPath === '/' || currentPath.startsWith('/portees')
  }
  return currentPath.startsWith(entry.path)
}
