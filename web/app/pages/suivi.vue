<template>
  <UiTabScreen title="Suivi" subtitle="Tes échanges avec les éleveurs, et qui rappeler.">
    <div class="flex flex-col gap-[26px]">
      <FollowUpTodayCard v-if="todayFollowUp" :follow-up="todayFollowUp" @open="followUpsStore.open" />

      <UiEmptyStateCard
        v-if="!followUpsStore.isLoading && followUpsStore.cards.length === 0"
        title="Aucune portée suivie"
        description="Touche « Suivre » sur une portée : elle arrive ici, avec ses rappels et tes notes."
      >
        <template #illustration>
          <UiMockupIcon name="heart" :size-in-pixels="36" :stroke-width="2" class="shrink-0 text-coral" />
        </template>
      </UiEmptyStateCard>

      <template v-else>
        <section v-for="section in visibleSections" :key="section.title" class="flex flex-col gap-3">
          <h2 class="m-0 font-display text-[22px] font-semibold">{{ section.title }}</h2>
          <FollowUpLitterCard
            v-for="followUp in cardsOf(section)"
            :key="followUp.litter.id"
            :follow-up="followUp"
            :is-note-shown="section.title === 'En discussion'"
            @open="followUpsStore.open"
          />
          <div
            v-if="cardsOf(section).length === 0 && section.emptyMessage"
            class="flex items-center gap-4 rounded-card-compact border-2 border-dashed border-line-strong px-[22px] py-5 text-base text-ink-muted"
          >
            <UiMockupIcon name="truffle" :size-in-pixels="38" class="shrink-0 text-line-strong" />
            <span>{{ section.emptyMessage }}</span>
          </div>
        </section>
      </template>
    </div>
    <FollowUpDrawer />
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { FollowUpCard } from '~/types/api'
import type { FollowUpSection } from '~/utils/followUpPresentation'
import { computed, onMounted } from 'vue'
import { FOLLOW_UP_SECTIONS, FollowUpPresentation } from '~/utils/followUpPresentation'

useHead({ title: 'Suivi · La Bonne Truffe' })

const followUpsStore: ReturnType<typeof useFollowUpsStore> = useFollowUpsStore()

const todayFollowUp: ComputedRef<FollowUpCard | null> = computed(
  (): FollowUpCard | null =>
    followUpsStore.cards.find((card: FollowUpCard): boolean => FollowUpPresentation.isDue(card, new Date())) ?? null,
)

const visibleSections: ComputedRef<readonly FollowUpSection[]> = computed((): readonly FollowUpSection[] =>
  FOLLOW_UP_SECTIONS.filter(
    (section: FollowUpSection): boolean => section.emptyMessage !== null || cardsOf(section).length > 0,
  ),
)

/**
 * Follow-ups of a section, in the order of the API (next reminder first).
 *
 * @param section - The section.
 * @returns Its cards.
 */
function cardsOf(section: FollowUpSection): FollowUpCard[] {
  return followUpsStore.cards.filter((card: FollowUpCard): boolean => section.statuses.includes(card.status))
}

onMounted((): void => {
  void followUpsStore.load()
})
</script>
