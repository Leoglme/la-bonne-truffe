<template>
  <UiTabScreen title="Notifications" subtitle="Ce que la truffe t’a signalé.">
    <div class="flex flex-col gap-3">
      <p v-if="bellStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ bellStore.loadError }}
      </p>
      <UiEmptyStateCard
        v-else-if="!bellStore.isLoading && bellStore.notifications.length === 0"
        title="Rien pour l’instant"
        description="Une portée préférée, une naissance ou le récap du soir s’afficheront ici."
      >
        <template #illustration>
          <UiCustomIcon name="bell" :size-in-pixels="36" :stroke-width="2" class="shrink-0 text-coral" />
        </template>
      </UiEmptyStateCard>
      <div
        v-else-if="bellStore.isLoading && bellStore.notifications.length === 0"
        aria-busy="true"
        aria-label="Chargement des notifications"
        class="flex flex-col gap-3"
      >
        <USkeleton v-for="placeholder in 3" :key="placeholder" class="h-[84px] rounded-card-compact" />
      </div>
      <NuxtLink
        v-for="notification in bellStore.notifications"
        :key="notification.id"
        :to="notification.url"
        class="flex flex-col gap-1 rounded-card-compact bg-card px-[22px] py-4 text-ink no-underline shadow-card hover:text-ink"
      >
        <span class="flex items-center justify-between gap-3 text-[13px]">
          <span class="font-extrabold">{{ notification.title }}</span>
          <span class="text-ink-muted">{{ formatTimeSinceSent(notification.sent_at) }}</span>
        </span>
        <span class="text-[15px] leading-[1.4]">{{ notification.body }}</span>
      </NuxtLink>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'
import { FrenchDate } from '~/utils/frenchDate'

useHead({ title: 'Notifications · La Bonne Truffe' })

const bellStore: ReturnType<typeof useBellStore> = useBellStore()

/**
 * Write how long ago a notification was sent.
 *
 * @param sentAt - Sending time, from the API.
 * @returns « il y a 12 min ».
 */
function formatTimeSinceSent(sentAt: string): string {
  return FrenchDate.formatTimeSince(FrenchDate.parseApiDate(sentAt), new Date())
}

onMounted(async (): Promise<void> => {
  await bellStore.load()
  if (bellStore.unreadCount > 0) {
    await bellStore.markAllRead()
  }
})
</script>
