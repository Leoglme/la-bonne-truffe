/** The badge on the icon of the installed app (iOS 16.4 and later): the unread notifications. */
export class AppBadge {
  /**
   * Put the unread count on the icon, or clear the badge at zero; a browser without the API ignores it.
   *
   * @param unreadCount - Unread notifications.
   */
  static async setUnreadCount(unreadCount: number): Promise<void> {
    if (!import.meta.client || !('setAppBadge' in navigator)) {
      return
    }
    try {
      if (unreadCount > 0) {
        await navigator.setAppBadge(unreadCount)
      } else {
        await navigator.clearAppBadge()
      }
    } catch {
      return
    }
  }
}
