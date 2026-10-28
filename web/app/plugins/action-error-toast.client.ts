import type { NuxtApp } from '#app'

/** Shows in a red toast every error that an action lets through: a button, the follow-up drawer, an update. */
export default defineNuxtPlugin((nuxtApp: NuxtApp): void => {
  const toast: ReturnType<typeof useToast> = useToast()

  nuxtApp.hook('vue:error', (error: unknown): void => {
    toast.add({
      title: error instanceof Error ? error.message : 'Une erreur est survenue',
      color: 'error',
      icon: 'i-lucide-circle-alert',
    })
  })
})
