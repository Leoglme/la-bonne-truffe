/**
 * Restore the session saved on this device before the first navigation. Client only.
 */
export default defineNuxtPlugin((): void => {
  useUserStore().restoreSession()
})
