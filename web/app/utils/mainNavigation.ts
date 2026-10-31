import type { MainNavigationEntry } from '~/types/MainNavigation'
import { SIDE_PANEL_MEDIA_QUERY } from '~/constants/mainNavigation'

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
      return currentPath === '/' || currentPath === '/carte' || currentPath.startsWith('/portees')
    }
    return currentPath.startsWith(entry.path)
  }

  /**
   * Whether the screen is wide enough for the side panel that shows the selected card.
   *
   * @returns True on a wide desktop.
   */
  static isSidePanelShown(): boolean {
    return window.matchMedia(SIDE_PANEL_MEDIA_QUERY).matches
  }
}
