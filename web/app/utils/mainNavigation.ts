import type { MainNavigationEntry } from '~/types/MainNavigation'

/** Which entry of the tab bar and of the sidebar matches the current screen. */
export class MainNavigation {
  /**
   * Whether an entry leads to the current screen or to one of its sub-screens.
   *
   * @param entry - The entry.
   * @param currentPath - Path of the current route.
   * @returns True for the active entry.
   */
  static isEntryActive(entry: MainNavigationEntry, currentPath: string): boolean {
    if (entry.path === '/') {
      return currentPath === '/' || currentPath.startsWith('/portees')
    }
    return currentPath.startsWith(entry.path)
  }
}
