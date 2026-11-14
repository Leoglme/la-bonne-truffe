import type { DeviceLocationLaunchFacts } from '~/types/Location'

/** When a launch of the app reads the position of the device by itself, without the person asking for it. */
export class DeviceLocationLaunch {
  /**
   * Tell whether a launch reads the position: once at first, then only while the device allows it without asking.
   *
   * @param facts - What the app kept on this device, and what the device tells of its permission.
   * @returns True when the launch reads the position.
   */
  static shouldReadPosition(facts: DeviceLocationLaunchFacts): boolean {
    if (facts.savedPermission === 'denied' || !facts.isPositionStale) {
      return false
    }
    if (!facts.hasSavedPosition) {
      return true
    }
    return facts.devicePermissionState === 'granted'
  }
}
