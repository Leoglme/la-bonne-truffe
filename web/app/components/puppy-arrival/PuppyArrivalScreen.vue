<template>
  <div v-if="puppyArrivalStore.arrival" class="mx-auto flex w-full max-w-2xl flex-col gap-6 md:gap-7">
    <div class="relative h-[250px] overflow-hidden rounded-card md:h-[320px]">
      <LitterTileFrame v-if="puppyArrivalStore.litter" :litter="puppyArrivalStore.litter" class="size-full">
        <LitterVisual
          :litter="puppyArrivalStore.litter"
          :illustration-size-in-pixels="170"
          photo-position="center 30%"
          photo-loading="eager"
        />
      </LitterTileFrame>
      <span v-else class="flex size-full items-center justify-center bg-gold-pastel">
        <CockerIllustration coat="gold" :size-in-pixels="170" />
      </span>
      <span
        v-if="countdownBadge"
        class="absolute top-3.5 left-3.5 rounded-full bg-coral px-3.5 py-1.5 font-display text-[17px] font-semibold text-white shadow-floating-over-photo"
      >
        {{ countdownBadge }}
      </span>
    </div>

    <div class="flex flex-col gap-1">
      <span class="text-xs font-extrabold tracking-[0.04em] text-coral-text uppercase md:text-sm">
        {{ arrivalDayLabel }}
      </span>
      <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[36px]">{{ title }}</h1>
      <p class="m-0 text-[15px] text-ink-muted md:text-[17px]">
        {{ PuppyArrivalPresentation.buildSentence(puppyArrivalStore.litter) }}
      </p>
    </div>

    <section class="flex flex-col gap-2.5 rounded-tile bg-card px-[18px] py-4 shadow-card">
      <div class="flex items-baseline justify-between gap-3">
        <h2 class="m-0 font-display text-xl font-semibold">Avant son arrivée</h2>
        <span class="text-[13px] font-extrabold text-ink-muted">
          {{ donePreparationCount }} sur {{ preparationCount }}
        </span>
      </div>
      <div
        role="progressbar"
        :aria-valuenow="donePreparationCount"
        aria-valuemin="0"
        :aria-valuemax="preparationCount"
        aria-label="Préparatifs faits"
        class="h-1.5 overflow-hidden rounded-full bg-line"
      >
        <span
          class="block h-full rounded-full bg-coral"
          :style="{ width: `${(donePreparationCount / preparationCount) * 100}%` }"
        />
      </div>
    </section>

    <section v-for="section in PUPPY_ARRIVAL_CHECKLIST" :key="section.title" class="flex flex-col gap-2">
      <h3 class="m-0 mb-0.5 text-xs font-extrabold tracking-[0.04em] text-ink-label uppercase">{{ section.title }}</h3>
      <label
        v-for="preparation in section.preparations"
        :key="preparation.key"
        class="flex min-h-[52px] cursor-pointer items-center gap-3 rounded-tile-compact bg-card px-4 py-2.5 shadow-card"
      >
        <input
          type="checkbox"
          :checked="puppyArrivalStore.arrival.done_items.includes(preparation.key)"
          class="size-[22px] shrink-0 accent-coral"
          @change="puppyArrivalStore.togglePreparation(preparation.key)"
        />
        <span class="flex flex-col">
          <span
            class="text-[15px] font-bold"
            :class="puppyArrivalStore.arrival.done_items.includes(preparation.key) ? 'text-ink-label line-through' : ''"
          >
            {{ preparation.label }}
          </span>
          <span v-if="preparation.description" class="text-[13px] text-ink-muted">{{ preparation.description }}</span>
        </span>
      </label>
    </section>

    <div
      v-if="!isResumeConfirmShown"
      class="flex flex-wrap items-center justify-center gap-x-1.5 pb-2 text-[13px] text-ink-muted"
    >
      <span>{{ PuppyArrivalPresentation.buildPausedLine(puppyArrivalStore.arrival.paused_since) }} ·</span>
      <button
        type="button"
        class="min-h-11 border-0 bg-transparent px-1 font-extrabold text-coral-text"
        @click="isResumeConfirmShown = true"
      >
        Reprendre la recherche
      </button>
    </div>
    <UiInlineConfirmation
      v-else
      question="Reprendre la recherche ?"
      consequence="Les alertes reviennent, et ta liste de préparatifs est effacée."
      confirm-label="Reprendre"
      :confirm-action="puppyArrivalStore.resumeSearch"
      @cancelled="isResumeConfirmShown = false"
    />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref } from 'vue'
import { PUPPY_ARRIVAL_CHECKLIST, PUPPY_ARRIVAL_CHECKLIST_KEYS } from '~/constants/puppyArrivalChecklist'
import { PuppyArrivalPresentation } from '~/utils/puppyArrivalPresentation'

const puppyArrivalStore: ReturnType<typeof usePuppyArrivalStore> = usePuppyArrivalStore()

const preparationCount: number = PUPPY_ARRIVAL_CHECKLIST_KEYS.length

const isResumeConfirmShown: Ref<boolean> = ref(false)

const daysLeft: ComputedRef<number> = computed((): number =>
  puppyArrivalStore.arrival
    ? PuppyArrivalPresentation.countDaysLeft(puppyArrivalStore.arrival.arrival_on, new Date())
    : 0,
)
const countdownBadge: ComputedRef<string | null> = computed((): string | null =>
  PuppyArrivalPresentation.buildCountdownBadge(daysLeft.value),
)
const arrivalDayLabel: ComputedRef<string> = computed((): string =>
  puppyArrivalStore.arrival
    ? PuppyArrivalPresentation.buildArrivalDayLabel(puppyArrivalStore.arrival.arrival_on, daysLeft.value)
    : '',
)
const title: ComputedRef<string> = computed((): string => PuppyArrivalPresentation.buildTitle(daysLeft.value))
const donePreparationCount: ComputedRef<number> = computed((): number =>
  PuppyArrivalPresentation.countDonePreparations(puppyArrivalStore.arrival?.done_items ?? []),
)
</script>
