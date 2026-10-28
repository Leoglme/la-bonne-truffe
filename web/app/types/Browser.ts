export type IosNavigator = Navigator & {
  standalone?: boolean
}

export type TauriWindow = Window & {
  __TAURI_INTERNALS__?: unknown
}

export type ServiceWorkerMessage = {
  type?: unknown
  url?: unknown
}
