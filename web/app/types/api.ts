import type { components } from '~/types/api.generated'

type Schemas = components['schemas']

export type User = Schemas['UserResponse']
export type LoginCredentials = Schemas['UserLogin']
export type TokenResponse = Schemas['Token']
export type VapidKeyResponse = Schemas['VapidKeyResponse']
export type PushSubscriptionPayload = Schemas['PushSubscriptionCreate']
export type TestNotificationResult = Schemas['TestNotificationResult']
export type NotificationHistory = Schemas['NotificationListResponse']
export type SentNotification = Schemas['NotificationResponse']
