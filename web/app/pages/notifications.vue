<template>
  <UiTabScreen title="Notifications" :subtitle="subtitle">
    <div class="flex flex-col gap-6">
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
        <USkeleton v-for="placeholder in 3" :key="placeholder" class="h-[96px] rounded-card-compact" />
      </div>
      <section v-for="section in daySections" :key="section.key" class="flex flex-col gap-2.5">
        <h2 class="m-0 font-display text-[22px] font-semibold">{{ section.title }}</h2>
        <template v-for="notification in section.notifications" :key="notification.id">
          <NotificationDigestCard v-if="notification.kind === 'evening_digest'" :notification="notification" />
          <NotificationCard v-else :notification="notification" />
        </template>
      </section>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { NotificationDaySection } from '~/types/Notification'
import { computed, onMounted, ref } from 'vue'
import { FrenchText } from '~/utils/frenchText'
import { NotificationPresentation } from '~/utils/notificationPresentation'

useHead({ title: 'Notifications · La Bonne Truffe' })

const bellStore: ReturnType<typeof useBellStore> = useBellStore()

const newNotificationCount: Ref<number> = ref(0)

const daySections: ComputedRef<NotificationDaySection[]> = computed((): NotificationDaySection[] =>
  NotificationPresentation.groupByDay(bellStore.notifications, new Date()),
)
const subtitle: ComputedRef<string> = computed((): string => {
  if (newNotificationCount.value === 0) {
    return 'Ce que la truffe t’a signalé.'
  }
  const count: string = FrenchText.spellOutCount(newNotificationCount.value, 'feminine')
  return `${count} ${FrenchText.pickForm(newNotificationCount.value, 'nouvelle', 'nouvelles')} depuis ta dernière visite.`
})

onMounted(async (): Promise<void> => {
  await bellStore.load()
  newNotificationCount.value = bellStore.unreadCount
  if (bellStore.unreadCount > 0) {
    await bellStore.markAllRead()
  }
})
</script>
