import type { MainNavigationEntry, PushedScreenBackLabel } from '~/types/MainNavigation'
import { MAIN_NAVIGATION_ENTRIES, PUSHED_SCREEN_BACK_LABELS, SIDE_PANEL_MEDIA_QUERY } from '~/constants/mainNavigation'

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

  /**
   * Name the screen the back button of a pushed screen returns to.
   *
   * @param previousPath - Path of the screen it was opened from, or null when the app started on it.
   * @param fallbackLabel - The name when there is no previous screen, or when it is not known.
   * @returns « Suivi », « La portée », « Notifications »…
   */
  static buildBackLabel(previousPath: string | null, fallbackLabel: string): string {
    if (previousPath === null) {
      return fallbackLabel
    }
    const path: string = previousPath.split(/[?#]/)[0] ?? previousPath
    const pushedScreen: PushedScreenBackLabel | undefined = PUSHED_SCREEN_BACK_LABELS.find(
      (screen: PushedScreenBackLabel): boolean => screen.pathPattern.test(path),
    )
    if (pushedScreen !== undefined) {
      return pushedScreen.label
    }
    const entry: MainNavigationEntry | undefined = MAIN_NAVIGATION_ENTRIES.find(
      (candidate: MainNavigationEntry): boolean => MainNavigation.isEntryActive(candidate, path),
    )
    return entry?.label ?? fallbackLabel
  }
}
