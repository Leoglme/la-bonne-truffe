<template>
  <UiTabScreen title="Notifications" subtitle="Ce que la truffe t’a signalé.">
    <div class="flex flex-col gap-3">
      <UiEmptyStateCard
        v-if="bellStore.notifications.length === 0"
        title="Rien pour l’instant"
        description="Une portée préférée, une naissance ou le récap du soir s’afficheront ici."
      >
        <template #illustration>
          <UiMockupIcon name="bell" :size-in-pixels="36" :stroke-width="2" class="shrink-0 text-coral" />
        </template>
      </UiEmptyStateCard>
      <NuxtLink
        v-for="notification in bellStore.notifications"
        :key="notification.id"
        :to="notification.url"
        class="flex flex-col gap-1 rounded-card-compact bg-card px-[22px] py-4 text-ink no-underline shadow-card hover:text-ink"
      >
        <span class="flex items-center justify-between gap-3 text-[13px]">
          <span class="font-extrabold">{{ notification.title }}</span>
          <span class="text-ink-muted">{{ RelativeTime.since(new Date(`${notification.sent_at}Z`), new Date()) }}</span>
        </span>
        <span class="text-[15px] leading-[1.4]">{{ notification.body }}</span>
      </NuxtLink>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'
import { RelativeTime } from '~/utils/relativeTime'

useHead({ title: 'Notifications · La Bonne Truffe' })

const bellStore: ReturnType<typeof useBellStore> = useBellStore()

onMounted(async (): Promise<void> => {
  await bellStore.load()
  if (bellStore.unreadCount > 0) {
    await bellStore.markAllRead()
  }
})
</script>
