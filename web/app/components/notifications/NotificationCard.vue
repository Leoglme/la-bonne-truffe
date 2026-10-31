<template>
  <article class="flex flex-col rounded-card-compact bg-card p-3 shadow-card">
    <NuxtLink :to="props.notification.url" class="flex gap-3 text-ink no-underline hover:text-ink">
      <LitterTileFrame v-if="litter" :litter="litter" class="size-16 overflow-hidden rounded-2xl">
        <LitterVisual :litter="litter" :illustration-size-in-pixels="46" />
      </LitterTileFrame>
      <span
        v-else-if="iconTile"
        class="inline-flex size-16 shrink-0 items-center justify-center rounded-2xl"
        :class="iconTile.tileClass"
      >
        <UIcon :name="iconTile.iconName" class="size-7" />
      </span>
      <span class="flex min-w-0 grow flex-col gap-0.5">
        <NotificationHeaderLine
          :kind="props.notification.kind"
          :sent-at="props.notification.sent_at"
          :is-unread="props.notification.read_at === null"
        />
        <span class="font-display text-[17px] leading-[1.2] font-semibold" :class="litter ? 'truncate' : ''">
          {{ headline }}
        </span>
        <span v-if="litter && litterFact" class="flex flex-wrap items-center gap-x-1 text-sm leading-[1.35]">
          <span>{{ litterFact }}</span>
          <span v-if="hasSexesShown" class="inline-flex items-center gap-1 whitespace-nowrap">
            <span aria-hidden="true">·</span>
            <LitterSexCounts :litter="litter" />
          </span>
          <template v-if="availabilityFact">
            <span aria-hidden="true">·</span>
            <span>{{ availabilityFact }}</span>
          </template>
        </span>
        <span v-else class="text-sm leading-[1.35]">{{ props.notification.body }}</span>
        <span v-if="litter" class="text-[13px] text-ink-muted">{{ placeAndColorLine }}</span>
      </span>
    </NuxtLink>
    <a
      v-if="phoneHref"
      :href="phoneHref"
      class="mt-2 ml-[76px] inline-flex min-h-9 items-center gap-1.5 self-start rounded-full bg-coral px-3.5 text-sm font-extrabold text-white no-underline"
    >
      <UiCustomIcon name="phone" :size-in-pixels="16" :stroke-width="2.2" class="size-4" />
      Appeler
    </a>
  </article>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { NotificationLitter, SentNotification } from '~/types/api'
import type { NotificationIconTile } from '~/types/Notification'
import type { NotificationCardProps } from '~/types/NotificationCard'
import { computed } from 'vue'
import { NOTIFICATION_ICON_TILES } from '~/constants/notificationKinds'
import { LitterPresentation } from '~/utils/litterPresentation'
import { NotificationPresentation } from '~/utils/notificationPresentation'

const props: NotificationCardProps = defineProps({
  notification: { type: Object as PropType<SentNotification>, required: true },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const litter: ComputedRef<NotificationLitter | null> = computed(
  (): NotificationLitter | null => props.notification.litter ?? null,
)
const iconTile: ComputedRef<NotificationIconTile | null> = computed(
  (): NotificationIconTile | null => NOTIFICATION_ICON_TILES[props.notification.kind] ?? null,
)
const headline: ComputedRef<string> = computed((): string => litter.value?.name ?? props.notification.title)
const litterFact: ComputedRef<string | null> = computed((): string | null => {
  if (litter.value === null) {
    return null
  }
  if (props.notification.kind === 'follow_up_reminder') {
    return 'C’est l’heure d’appeler l’éleveur.'
  }
  return NotificationPresentation.isLitterEvent(props.notification.kind)
    ? LitterPresentation.buildBirthFact(litter.value)
    : null
})
const hasSexesShown: ComputedRef<boolean> = computed(
  (): boolean =>
    litter.value !== null &&
    litter.value.kind !== 'litter_expected' &&
    NotificationPresentation.isLitterEvent(props.notification.kind),
)
const availabilityFact: ComputedRef<string | null> = computed((): string | null =>
  litter.value && NotificationPresentation.isLitterEvent(props.notification.kind)
    ? NotificationPresentation.buildAvailabilityFact(litter.value)
    : null,
)
const placeAndColorLine: ComputedRef<string> = computed((): string =>
  litter.value ? NotificationPresentation.buildPlaceAndColorLine(litter.value, locationStore.position) : '',
)
const phoneHref: ComputedRef<string | null> = computed((): string | null => {
  const phone: string | null = litter.value?.breeder_phone_e164 ?? null
  return props.notification.kind === 'follow_up_reminder' && phone !== null ? `tel:${phone}` : null
})
</script>
