import type { RouteLocationNormalized } from 'vue-router'

/** The only page reachable without a session. */
const LOGIN_PATH: string = '/connexion'

/**
 * Keep every page behind the session; send a signed-in user away from the login page.
 * Runs on the client only: the session lives in localStorage.
 */
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
