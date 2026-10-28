import type { RouteLocationNormalized } from 'vue-router'

const LOGIN_PATH: string = '/connexion'

/** Keeps every page behind the session and sends a signed-in user away from the login page, on the client only. */
export default defineNuxtRouteMiddleware(async (to: RouteLocationNormalized) => {
  if (!import.meta.client) {
    return
  }
  const userStore: ReturnType<typeof useUserStore> = useUserStore()
  const hasValidSession: boolean = await userStore.validateSession()

  if (to.path === LOGIN_PATH) {
    return hasValidSession ? navigateTo('/') : undefined
  }
  if (!hasValidSession) {
    return navigateTo(LOGIN_PATH)
  }
})
