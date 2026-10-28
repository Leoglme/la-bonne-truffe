<template>
  <UiTabScreen title="Suivi" subtitle="Tes échanges avec les éleveurs, et qui rappeler.">
    <div class="flex flex-col gap-[26px]">
      <FollowUpTodayCard v-if="todayFollowUp" :follow-up="todayFollowUp" />

      <p v-if="followUpsStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ followUpsStore.loadError }}
      </p>
      <UiEmptyStateCard
        v-else-if="!followUpsStore.isLoading && followUpsStore.cards.length === 0"
        title="Aucune portée suivie"
        description="Touche « Suivre » sur une portée : elle arrive ici, avec ses rappels et tes notes."
      >
        <template #illustration>
          <UiCustomIcon name="heart" :size-in-pixels="36" :stroke-width="2" class="shrink-0 text-coral" />
        </template>
      </UiEmptyStateCard>

      <template v-else-if="followUpsStore.cards.length > 0">
        <section v-for="section in visibleSections" :key="section.title" class="flex flex-col gap-3">
          <h2 class="m-0 font-display text-[22px] font-semibold">{{ section.title }}</h2>
          <FollowUpLitterCard
            v-for="followUp in listSectionFollowUps(section)"
            :key="followUp.litter.id"
            :follow-up="followUp"
            :is-note-shown="section.title === 'En discussion'"
          />
          <div
            v-if="listSectionFollowUps(section).length === 0 && section.emptyMessage"
            class="flex items-center gap-4 rounded-card-compact border-2 border-dashed border-line-strong px-[22px] py-5 text-base text-ink-muted"
          >
            <UiCustomIcon name="truffle" :size-in-pixels="38" class="shrink-0 text-line-strong" />
            <span>{{ section.emptyMessage }}</span>
          </div>
        </section>
      </template>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { FollowUpCard } from '~/types/api'
import type { FollowUpSection } from '~/types/FollowUp'
import { computed, onMounted } from 'vue'
import { FOLLOW_UP_SECTIONS } from '~/constants/followUpOptions'
import { FollowUpPresentation } from '~/utils/followUpPresentation'

useHead({ title: 'Suivi · La Bonne Truffe' })

const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()

const todayFollowUp: ComputedRef<FollowUpCard | null> = computed(
  (): FollowUpCard | null =>
    followUpsStore.cards.find((card: FollowUpCard): boolean => FollowUpPresentation.isDue(card, new Date())) ?? null,
)

const visibleSections: ComputedRef<FollowUpSection[]> = computed((): FollowUpSection[] =>
  FOLLOW_UP_SECTIONS.filter(
    (section: FollowUpSection): boolean => section.emptyMessage !== null || listSectionFollowUps(section).length > 0,
  ),
)

/**
 * List the follow-ups of a section, in the order of the API (next reminder first).
 *
 * @param section - The section.
 * @returns Its cards.
 */
function listSectionFollowUps(section: FollowUpSection): FollowUpCard[] {
  return followUpsStore.cards.filter((card: FollowUpCard): boolean => section.statuses.includes(card.status))
}

onMounted((): Promise<void> => followUpsStore.load())
</script>
