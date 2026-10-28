<template>
  <UiTabScreen
    title="Notifications"
    subtitle="Une portée préférée qui apparaît, une portée suivie qui naît : la truffe te prévient tout de suite."
  >
    <div class="flex flex-col gap-[22px]">
      <NuxtLink to="/reglages" class="inline-flex items-center gap-1.5 self-start text-[15px] font-extrabold">
        <UiMockupIcon name="chevron-left" :size-in-pixels="18" :stroke-width="2.4" />
        Réglages
      </NuxtLink>

      <section class="flex flex-col gap-4 rounded-[26px] bg-card px-[22px] py-5 shadow-card">
        <div class="flex items-center justify-between gap-4">
          <span class="flex min-w-0 flex-col">
            <span class="text-[17px] font-bold">Sur cet appareil</span>
            <span class="text-sm text-ink-muted">{{ hint }}</span>
          </span>
          <UiToggleSwitch
            v-if="isSupported && !config.public.isDesktop"
            :model-value="isSubscribed"
            :is-disabled="isBusy"
            label="Notifications sur cet appareil"
            @update:model-value="toggle"
          />
        </div>
        <button
          v-if="isSubscribed"
          type="button"
          class="box-content min-h-11 self-start rounded-full border-2 border-ink bg-transparent px-[18px] text-[15px] font-extrabold text-ink disabled:opacity-60"
          :disabled="isSendingTest"
          @click="sendTestNotification"
        >
          {{ isSendingTest ? 'Envoi…' : 'Envoyer une notification de test' }}
        </button>
      </section>

      <section
        v-if="isSupported && !isStandalone && !config.public.isDesktop"
        class="flex flex-col gap-2 rounded-[26px] bg-coral-pastel px-[22px] py-5"
      >
        <h2 class="m-0 font-display text-[22px] font-semibold">Sur iPhone et iPad</h2>
        <p class="m-0 text-[15px] text-ink-secondary">
          Ajoute d’abord La Bonne Truffe à ton écran d’accueil : bouton <strong>Partager</strong>, puis
          <strong>« Sur l’écran d’accueil »</strong>. Rouvre ensuite l’app depuis son icône et active le bouton
          ci-dessus.
        </p>
      </section>
    </div>
  </UiTabScreen>
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
