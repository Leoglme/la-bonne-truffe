import type { RouteLocationNormalized } from 'vue-router'

const LOGIN_PATH: string = '/connexion'

/**
 * Keeps every page behind the session except the screens a visitor needs to get in, and sends a signed-in user
 * away from the login and signup screens. Client only: the session lives in localStorage.
 */
export default defineNuxtRouteMiddleware(async (to: RouteLocationNormalized) => {
  if (!import.meta.client) {
    return
  }
  const userStore: ReturnType<typeof useUserStore> = useUserStore()
  const hasValidSession: boolean = await userStore.validateSession()

  if (to.meta.isGuestOnlyScreen === true) {
    return hasValidSession ? navigateTo('/') : undefined
  }
  if (!hasValidSession && to.meta.isPublicScreen !== true) {
    return navigateTo(LOGIN_PATH)
  }
})
