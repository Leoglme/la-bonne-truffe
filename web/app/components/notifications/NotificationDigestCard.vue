<template>
  <article class="flex flex-col gap-3.5 rounded-card-compact bg-card px-3.5 pt-3.5 pb-4 shadow-card">
    <NotificationHeaderLine
      :kind="props.notification.kind"
      :sent-at="props.notification.sent_at"
      :is-unread="props.notification.read_at === null"
    />
    <span class="font-display text-[17px] leading-[1.2] font-semibold">{{ headline }}</span>
    <NuxtLink
      v-for="litter in acceptableLitters"
      :key="litter.id"
      :to="`/portees/${litter.id}`"
      class="flex items-center gap-2.5 text-ink no-underline hover:text-ink"
    >
      <LitterTileFrame :litter="litter" class="size-[42px] overflow-hidden rounded-xl">
        <LitterVisual :litter="litter" :illustration-size-in-pixels="32" />
      </LitterTileFrame>
      <span class="flex min-w-0 grow flex-col">
        <span class="truncate font-display text-[15px] font-semibold">{{ litter.name }}</span>
        <span class="flex flex-wrap items-center gap-x-1 text-[13px] text-ink-muted">
          <span>{{ NotificationPresentation.buildPlaceAndColorLine(litter, locationStore.position) }}</span>
          <span v-if="litter.kind !== 'litter_expected'" class="inline-flex items-center gap-1 whitespace-nowrap">
            <span aria-hidden="true">·</span>
            <LitterSexCounts :litter="litter" />
          </span>
        </span>
      </span>
      <span v-if="litter.score !== null" class="shrink-0 text-[13px] font-extrabold text-coral-text">
        {{ litter.score }} %
      </span>
    </NuxtLink>
    <NuxtLink
      v-for="litter in followedLitters"
      :key="litter.id"
      :to="`/portees/${litter.id}`"
      class="flex items-center gap-2 border-t border-line pt-3 text-sm leading-[1.35] text-ink no-underline hover:text-ink"
    >
      <UiCustomIcon name="heart" :size-in-pixels="18" :stroke-width="2" class="size-[18px] shrink-0 text-coral" />
      <span>
        <span class="font-extrabold">{{ litter.name }}</span
        >, {{ NotificationPresentation.buildPuppiesLeftPhrase(litter) }}.
      </span>
    </NuxtLink>
    <span v-if="props.notification.litters.length === 0" class="text-sm leading-[1.35]">
      {{ props.notification.body }}
    </span>
  </article>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { NotificationLitter, SentNotification } from '~/types/api'
import type { NotificationDigestCardProps } from '~/types/NotificationDigestCard'
import { computed } from 'vue'
import { FrenchText } from '~/utils/frenchText'
import { NotificationPresentation } from '~/utils/notificationPresentation'

const props: NotificationDigestCardProps = defineProps({
  notification: { type: Object as PropType<SentNotification>, required: true },
})

const locationStore: ReturnType<typeof useLocationStore> = useLocationStore()

const acceptableLitters: ComputedRef<NotificationLitter[]> = computed((): NotificationLitter[] =>
  props.notification.litters.filter(
    (litter: NotificationLitter): boolean => litter.digest_event !== 'availability_change',
  ),
)
const followedLitters: ComputedRef<NotificationLitter[]> = computed((): NotificationLitter[] =>
  props.notification.litters.filter(
    (litter: NotificationLitter): boolean => litter.digest_event === 'availability_change',
  ),
)
const headline: ComputedRef<string> = computed((): string => {
  const count: number = acceptableLitters.value.length
  if (count === 0) {
    return 'Tes portées suivies'
  }
  return `${count} ${FrenchText.pickForm(count, 'portée acceptable', 'portées acceptables')}`
})
</script>
