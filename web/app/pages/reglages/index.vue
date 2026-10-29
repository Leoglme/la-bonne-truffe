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
useHead({ title: 'Réglages · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

/**
 * Forget the session on this device and go back to the login screen.
 */
async function logout(): Promise<void> {
  userStore.logout()
  await navigateTo('/connexion')
}
</script>
