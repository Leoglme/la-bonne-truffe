import type {
  NotificationHistory,
  PushSubscriptionPayload,
  TestNotificationResult,
  VapidKeyResponse,
} from '~/types/api'
import { ApiClient } from './api'

/** HTTP client for the /notifications API resource: Web Push subscription, test and bell history. */
export class NotificationsService {
  /**
   * Fetch the public VAPID key needed to subscribe.
   *
   * @returns The public key and whether push is configured server-side.
   */
  static async getVapidKey(): Promise<VapidKeyResponse> {
    return ApiClient.get<VapidKeyResponse>('/api/v1/notifications/vapid-key')
  }

  /**
   * Register (or refresh) a browser push subscription for the user.
   *
   * @param payload - Endpoint, encryption keys and device hint.
   */
  static async subscribe(payload: PushSubscriptionPayload): Promise<void> {
    await ApiClient.post('/api/v1/notifications/subscribe', payload)
  }

  /**
   * Remove a browser push subscription of the user.
   *
   * @param endpoint - The subscription endpoint to unregister.
   */
  static async unsubscribe(endpoint: string): Promise<void> {
    await ApiClient.delete('/api/v1/notifications/subscribe', { endpoint })
  }

  /**
   * Send a test notification now and return the delivery diagnostic.
   *
   * @returns Whether push is configured, the device count, and delivered/failed counts.
   */
  static async test(): Promise<TestNotificationResult> {
    return ApiClient.post<TestNotificationResult>('/api/v1/notifications/test', {})
  }

  /**
   * Fetch a page of the notification history, newest first, with the unread count.
   *
   * @param before - Return the notifications whose id is strictly below this one.
   * @returns The page and the unread count.
   */
  static async getHistory(before?: number): Promise<NotificationHistory> {
    return ApiClient.get<NotificationHistory>('/api/v1/notifications', { params: { before } })
  }
}
