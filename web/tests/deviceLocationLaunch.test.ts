import type { DeviceLocationLaunchFacts } from '../app/types/Location'
import { describe, expect, it } from 'vitest'
import { DeviceLocationLaunch } from '../app/utils/deviceLocationLaunch'

const STALE_POSITION_AT_A_LATER_LAUNCH: DeviceLocationLaunchFacts = {
  savedPermission: 'granted',
  hasSavedPosition: true,
  isPositionStale: true,
  devicePermissionState: 'prompt',
}

describe('DeviceLocationLaunch.shouldReadPosition', () => {
  it('asks for the position at the first launch', () => {
    expect(
      DeviceLocationLaunch.shouldReadPosition({
        savedPermission: 'unknown',
        hasSavedPosition: false,
        isPositionStale: true,
        devicePermissionState: 'prompt',
      }),
    ).toBe(true)
  })

  it('does not ask again when the iPhone forgot it allowed the app', () => {
    expect(DeviceLocationLaunch.shouldReadPosition(STALE_POSITION_AT_A_LATER_LAUNCH)).toBe(false)
  })

  it('does not ask again when the browser cannot tell the permission', () => {
    expect(
      DeviceLocationLaunch.shouldReadPosition({ ...STALE_POSITION_AT_A_LATER_LAUNCH, devicePermissionState: null }),
    ).toBe(false)
  })

  it('refreshes an old position while the device still allows it', () => {
    expect(
      DeviceLocationLaunch.shouldReadPosition({
        ...STALE_POSITION_AT_A_LATER_LAUNCH,
        devicePermissionState: 'granted',
      }),
    ).toBe(true)
  })

  it('keeps a recent position', () => {
    expect(
      DeviceLocationLaunch.shouldReadPosition({
        ...STALE_POSITION_AT_A_LATER_LAUNCH,
        isPositionStale: false,
        devicePermissionState: 'granted',
      }),
    ).toBe(false)
  })

  it('never asks after a refusal', () => {
    expect(
      DeviceLocationLaunch.shouldReadPosition({
        savedPermission: 'denied',
        hasSavedPosition: false,
        isPositionStale: true,
        devicePermissionState: 'prompt',
      }),
    ).toBe(false)
  })
})
