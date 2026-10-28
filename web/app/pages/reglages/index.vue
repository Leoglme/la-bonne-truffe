<template>
  <div class="flex flex-col gap-5 px-5 pt-[58px] pb-6 md:gap-7 md:px-8 md:pt-9 md:pb-8 lg:px-10">
    <UiPageHeader title="Réglages" subtitle="Notifications et compte." />

    <NuxtLink
      to="/reglages/notifications"
      class="flex min-h-14 items-center justify-between gap-3 rounded-card-compact bg-card px-[22px] py-4 text-ink no-underline shadow-card hover:text-ink"
    >
      <span class="flex flex-col">
        <span class="text-[17px] font-bold">Notifications</span>
        <span class="text-sm text-ink-muted">Sur l’iPhone et l’iPad, dès qu’une portée préférée apparaît</span>
      </span>
      <UIcon name="i-lucide-chevron-right" class="size-[22px] shrink-0" aria-hidden="true" />
    </NuxtLink>

    <section class="flex flex-col gap-3 rounded-card-compact bg-card px-[22px] py-5 shadow-card">
      <h2 class="m-0 font-display text-xl font-semibold md:text-[22px]">Compte</h2>
      <p class="m-0 text-[15px] text-ink-muted">{{ userStore.user?.email }}</p>
      <UButton color="neutral" variant="outline" size="lg" class="self-start" @click="logout"> Se déconnecter </UButton>
    </section>
  </div>
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
