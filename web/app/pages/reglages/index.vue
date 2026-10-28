<template>
  <UiTabScreen title="Réglages" subtitle="Notifications, sources et compte.">
    <div class="flex flex-col gap-[22px]">
      <UiSettingsLinkCard
        to="/reglages/notifications"
        title="Notifications"
        description="Sur l’iPhone et l’iPad, dès qu’une portée préférée apparaît"
      />
      <UiSettingsLinkCard
        to="/sources"
        title="Sources"
        description="Dernier relevé de chaque site, et relevé à la main"
      />
      <UiSettingsLinkCard to="/notifications" title="Historique" description="Les notifications déjà reçues" />

      <section class="flex flex-col gap-3 rounded-[26px] bg-card px-[22px] py-5 shadow-card">
        <h2 class="m-0 font-display text-[22px] font-semibold">Compte</h2>
        <ClientOnly>
          <p class="m-0 text-[15px] text-ink-muted">{{ userStore.user?.email }}</p>
        </ClientOnly>
        <button
          type="button"
          class="box-content min-h-11 self-start rounded-full border-2 border-ink bg-transparent px-[18px] text-[15px] font-extrabold text-ink"
          @click="logout"
        >
          Se déconnecter
        </button>
      </section>
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
