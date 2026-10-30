import type { ComputedRef, Ref } from 'vue'
import type { DeviceLocationPermission, DevicePosition } from '~/types/Location'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const POSITION_STORAGE_KEY: string = 'lbt-position'
const PERMISSION_STORAGE_KEY: string = 'lbt-position-permission'
const POSITION_MAX_AGE_MS: number = 6 * 60 * 60_000
const POSITION_REQUEST_TIMEOUT_MS: number = 15_000
const POSITION_REUSE_MS: number = 60_000
const PERMISSIONS: DeviceLocationPermission[] = ['unknown', 'granted', 'denied', 'unavailable']

/** Pinia store of the position of the device, asked like a native app does and kept in localStorage. */
export const useLocationStore = defineStore('location', () => {
  const position: Ref<DevicePosition | null> = ref(null)
  const permission: Ref<DeviceLocationPermission> = ref('unknown')
  const isLocating: Ref<boolean> = ref(false)

  const isSupported: ComputedRef<boolean> = computed((): boolean => import.meta.client && 'geolocation' in navigator)
  const isPositionStale: ComputedRef<boolean> = computed(
    (): boolean =>
      position.value === null || Date.now() - new Date(position.value.recordedAt).getTime() > POSITION_MAX_AGE_MS,
  )

  /**
   * Restore the position and the permission kept on this device. Client only.
   */
  function restore(): void {
    if (!import.meta.client) {
      return
    }
    try {
      const savedPosition: string | null = localStorage.getItem(POSITION_STORAGE_KEY)
      position.value = savedPosition ? (JSON.parse(savedPosition) as DevicePosition) : null
      const savedPermission: string | null = localStorage.getItem(PERMISSION_STORAGE_KEY)
      permission.value =
        PERMISSIONS.find((candidate: DeviceLocationPermission): boolean => candidate === savedPermission) ?? 'unknown'
    } catch {
      position.value = null
      permission.value = 'unknown'
    }
  }

  /**
   * Ask the device for its position: the system asks the person the first time, as for any app.
   *
   * @returns True when a position was read.
   */
  async function request(): Promise<boolean> {
    if (!isSupported.value) {
      rememberPermission('unavailable')
      return false
    }
    if (isLocating.value) {
      return false
    }
    isLocating.value = true
    try {
      const coordinates: GeolocationCoordinates = await readCurrentCoordinates()
      rememberPosition({
        latitude: coordinates.latitude,
        longitude: coordinates.longitude,
        recordedAt: new Date().toISOString(),
      })
      rememberPermission('granted')
      return true
    } catch (error: unknown) {
      if (isPermissionDenied(error)) {
        rememberPermission('denied')
      } else if (permission.value !== 'granted') {
        rememberPermission('unavailable')
      }
      return false
    } finally {
      isLocating.value = false
    }
  }

  /**
   * At a launch, ask for the position the first time, and refresh a position older than a few hours.
   */
  async function refreshAtLaunch(): Promise<void> {
    if (permission.value === 'denied' || !isPositionStale.value) {
      return
    }
    await request()
  }

  /**
   * Read the current position of the device once.
   *
   * @returns The coordinates.
   * @throws GeolocationPositionError when the person refuses, or the device cannot tell in time.
   */
  function readCurrentCoordinates(): Promise<GeolocationCoordinates> {
    return new Promise(
      (
        resolve: (coordinates: GeolocationCoordinates) => void,
        reject: (error: GeolocationPositionError) => void,
      ): void => {
        navigator.geolocation.getCurrentPosition(
          (currentPosition: GeolocationPosition): void => resolve(currentPosition.coords),
          reject,
          { enableHighAccuracy: false, timeout: POSITION_REQUEST_TIMEOUT_MS, maximumAge: POSITION_REUSE_MS },
        )
      },
    )
  }

  /**
   * Whether an error of the device means the person refused.
   *
   * @param error - What the device raised.
   * @returns True for a refusal.
   */
  function isPermissionDenied(error: unknown): boolean {
    return error instanceof GeolocationPositionError && error.code === GeolocationPositionError.PERMISSION_DENIED
  }

  /**
   * Keep a position on this device.
   *
   * @param devicePosition - The position just read.
   */
  function rememberPosition(devicePosition: DevicePosition): void {
    position.value = devicePosition
    try {
      localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(devicePosition))
    } catch {
      return
    }
  }

  /**
   * Keep what the person answered on this device.
   *
   * @param answer - The permission state.
   */
  function rememberPermission(answer: DeviceLocationPermission): void {
    permission.value = answer
    try {
      localStorage.setItem(PERMISSION_STORAGE_KEY, answer)
    } catch {
      return
    }
  }

  return { position, permission, isLocating, isSupported, restore, request, refreshAtLaunch }
})
