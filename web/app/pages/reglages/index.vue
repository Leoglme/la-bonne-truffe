<template>
  <UiTabScreen title="Réglages" subtitle="Notifications, sources et compte.">
    <div class="flex flex-col gap-[22px]">
      <UiLinkCard
        to="/reglages/notifications"
        title="Notifications"
        description="Sur l’iPhone et l’iPad, dès qu’une portée préférée apparaît"
      />
      <UiLinkCard to="/sources" title="Sources" description="Dernier relevé de chaque site, et relevé à la main" />
      <UiLinkCard to="/notifications" title="Historique" description="Les notifications déjà reçues" />

      <UiSectionCard title="Position" class="gap-3">
        <ClientOnly>
          <p class="m-0 text-[15px] text-ink-muted">{{ locationStatusDescription }}</p>
          <UButton
            v-if="locationStore.isSupported"
            size="xl"
            class="w-full justify-center md:w-auto md:self-start"
            :loading="locationStore.isLocating"
            @click="locationStore.request()"
          >
            {{ positionButtonLabel }}
          </UButton>
        </ClientOnly>
      </UiSectionCard>

      <UiSectionCard title="Compte" class="gap-3">
        <ClientOnly>
          <p class="m-0 text-[15px] text-ink-muted">{{ userStore.user?.email }}</p>
        </ClientOnly>
        <UButton
          color="neutral"
          variant="outline"
          size="xl"
          class="w-full justify-center md:w-auto md:self-start"
          @click="logout"
        >
          Se déconnecter
        </UButton>
      </UiSectionCard>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import { computed } from 'vue'
import { FrenchDate } from '~/utils/frenchDate'

useHead({ title: 'Réglages · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()
const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const positionButtonLabel: ComputedRef<string> = computed((): string => {
  if (locationStore.permission === 'granted') {
    return 'Mettre à jour ma position'
  }
  return locationStore.permission === 'denied' ? 'Réessayer' : 'Autoriser ma position'
})
const locationStatusDescription: ComputedRef<string> = computed((): string => {
  if (!locationStore.isSupported) {
    return 'Cet appareil ne donne pas sa position.'
  }
  if (locationStore.permission === 'denied') {
    return 'Position refusée : autorise-la dans les réglages de l’appareil, puis réessaie, pour voir la distance de chaque portée.'
  }
  if (locationStore.position !== null) {
    const timeSinceReading: string = FrenchDate.formatTimeSince(new Date(locationStore.position.recordedAt), new Date())
    return `Position relevée ${timeSinceReading} : la distance s’affiche sur chaque portée.`
  }
  return 'Autorise ta position pour voir à quelle distance est chaque portée.'
})

/**
 * Forget the session on this device and go back to the login screen.
 */
async function logout(): Promise<void> {
  userStore.logout()
  await navigateTo('/connexion')
}
</script>
