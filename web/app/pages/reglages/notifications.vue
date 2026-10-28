<template>
  <div class="flex flex-col gap-5 px-5 pt-[58px] pb-6 md:gap-7 md:px-8 md:pt-9 md:pb-8 lg:px-10">
    <NuxtLink
      to="/reglages"
      aria-label="Retour aux réglages"
      class="inline-flex size-11 items-center justify-center rounded-full bg-card text-ink shadow-floating hover:text-ink md:size-[52px]"
    >
      <UIcon name="i-lucide-arrow-left" class="size-[22px]" aria-hidden="true" />
    </NuxtLink>

    <UiPageHeader
      title="Notifications"
      subtitle="Une portée préférée qui apparaît, une portée suivie qui naît : la truffe te prévient tout de suite."
    />

    <section class="flex flex-col gap-4 rounded-card-compact bg-card px-[22px] py-5 shadow-card">
      <div class="flex items-center justify-between gap-4">
        <span class="flex min-w-0 flex-col">
          <span id="push-switch-label" class="text-[17px] font-bold">Sur cet appareil</span>
          <span class="text-sm text-ink-muted">{{ hint }}</span>
        </span>
        <USwitch
          v-if="isSupported && !config.public.isDesktop"
          :model-value="isSubscribed"
          :disabled="isBusy"
          aria-labelledby="push-switch-label"
          @update:model-value="toggle"
        />
      </div>
      <UButton
        v-if="isSubscribed"
        color="neutral"
        variant="outline"
        size="lg"
        class="self-start"
        :loading="isSendingTest"
        @click="sendTestNotification"
      >
        Envoyer une notification de test
      </UButton>
    </section>

    <section
      v-if="isSupported && !isStandalone && !config.public.isDesktop"
      class="flex flex-col gap-2 rounded-card-compact bg-coral-pastel px-[22px] py-5"
    >
      <h2 class="m-0 font-display text-xl font-semibold">Sur iPhone et iPad</h2>
      <p class="m-0 text-[15px] text-ink-secondary">
        Ajoute d’abord La Bonne Truffe à ton écran d’accueil : bouton
        <strong>Partager</strong>
        <UIcon name="i-lucide-arrow-right" class="inline-block size-[1em] align-[-0.125em]" aria-hidden="true" />
        <strong>« Sur l’écran d’accueil »</strong>, puis rouvre l’app depuis son icône et active le bouton ci-dessus.
      </p>
    </section>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { UseWebPush } from '~/composables/useWebPush'
import type { TestNotificationResult } from '~/types/api'
import { computed, ref } from 'vue'

useHead({ title: 'Notifications · La Bonne Truffe' })

const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
const toast: ReturnType<typeof useToast> = useToast()
const { isSupported, isStandalone, isSubscribed, isBusy, error, toggle, sendTest }: UseWebPush = useWebPush()

const isSendingTest: Ref<boolean> = ref(false)

const hint: ComputedRef<string> = computed((): string => {
  if (config.public.isDesktop) {
    return 'Les notifications arrivent sur l’iPhone et l’iPad où l’app est installée.'
  }
  if (!isSupported.value) {
    return 'Ce navigateur ne reçoit pas les notifications push.'
  }
  if (error.value === 'permission') {
    return 'Permission refusée : autorise les notifications dans les réglages du navigateur.'
  }
  if (error.value === 'not-configured') {
    return 'Le serveur de notifications n’est pas encore configuré (clés VAPID).'
  }
  if (error.value === 'unexpected') {
    return 'Une erreur est survenue. Réessaie.'
  }
  if (!isStandalone.value) {
    return 'Sur iPhone et iPad, installe d’abord l’app (voir ci-dessous).'
  }
  return isSubscribed.value ? 'Activées : tu reçois les alertes ici.' : 'Désactivées sur cet appareil.'
})

/**
 * Send a test notification and tell the outcome in a toast.
 */
async function sendTestNotification(): Promise<void> {
  isSendingTest.value = true
  try {
    const result: TestNotificationResult = await sendTest()
    if (result.subscriptions === 0) {
      toast.add({ title: 'Aucun appareil abonné.', color: 'warning' })
    } else if (result.failed > 0) {
      toast.add({ title: result.detail ?? 'Le service push a refusé l’envoi.', color: 'error' })
    } else {
      toast.add({ title: `Notification de test envoyée (${result.delivered}).`, color: 'success' })
    }
  } catch {
    toast.add({ title: 'Échec de l’envoi du test.', color: 'error' })
  } finally {
    isSendingTest.value = false
  }
}
</script>
