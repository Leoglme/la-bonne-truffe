<template>
  <section v-if="props.breeder.reproducers.length > 0" class="flex flex-col gap-3">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Ses reproducteurs</h2>
      <span v-if="hasSitePhotos" class="text-[13px] font-bold text-ink-label md:text-sm">Photos de son site</span>
    </div>
    <ul
      class="m-0 list-none p-0"
      :class="
        props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-3' : 'flex flex-col gap-2.5'
      "
    >
      <li
        v-for="dog in shownDogs"
        :key="dog.id"
        class="flex items-start gap-3 rounded-[20px] bg-card py-3 pr-4 pl-3 shadow-card md:gap-4 md:rounded-[22px] md:pr-[18px]"
      >
        <DogPortrait
          :photo-url="dog.photos[0] ?? null"
          :color="dog.color"
          size-class="size-14 rounded-2xl md:size-[72px] md:rounded-[18px]"
          :illustration-size-in-pixels="DOG_ILLUSTRATION_SIZE_IN_PIXELS"
        />
        <span class="flex min-w-0 grow flex-col gap-0.5">
          <span class="flex min-h-6 items-center justify-between gap-2 md:min-h-7">
            <span class="text-[11px] font-extrabold tracking-[0.04em] text-ink-label uppercase md:text-[13px]">
              {{ BreederPresentation.buildDogRoleLabel(dog) }}
            </span>
            <span
              v-if="BreederPresentation.buildDogRatingLabel(dog)"
              class="inline-flex shrink-0 rounded-full bg-chip px-2.5 py-1 text-xs font-extrabold whitespace-nowrap text-ink-secondary md:px-3 md:text-[13px]"
            >
              {{ BreederPresentation.buildDogRatingLabel(dog) }}
            </span>
          </span>
          <component
            :is="dog.external_url ? 'a' : 'span'"
            :href="dog.external_url ?? undefined"
            :target="dog.external_url ? '_blank' : undefined"
            :rel="dog.external_url ? 'noopener' : undefined"
            class="text-[15px] font-bold text-ink no-underline md:text-[17px]"
          >
            {{ BreederPresentation.buildDogName(dog) }}
          </component>
          <span v-if="BreederPresentation.buildDogFactsLine(dog)" class="text-[13px] text-ink-muted md:text-sm">
            {{ BreederPresentation.buildDogFactsLine(dog) }}
          </span>
          <span v-if="dog.availability_text" class="text-[13px] font-bold text-coral-text md:text-sm">
            {{ dog.availability_text }}
          </span>
        </span>
      </li>
    </ul>
    <template v-if="hiddenDogsCount > 0">
      <a
        v-if="siteDogsUrl"
        :href="siteDogsUrl"
        target="_blank"
        rel="noopener"
        class="inline-flex min-h-[52px] items-center justify-between gap-3 rounded-[20px] bg-card px-[18px] text-[15px] font-bold text-ink-secondary no-underline shadow-card hover:text-ink-secondary md:text-base"
      >
        {{ BreederPresentation.buildHiddenDogsLabel(hiddenDogsCount, true) }}
        <UIcon name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
      </a>
      <button
        v-else
        type="button"
        class="inline-flex min-h-[52px] items-center justify-between gap-3 rounded-[20px] border-0 bg-card px-[18px] text-left text-[15px] font-bold text-ink shadow-card"
        @click="areAllDogsShown = true"
      >
        {{ BreederPresentation.buildHiddenDogsLabel(hiddenDogsCount, false) }}
        <UIcon name="i-lucide-chevron-right" class="size-5 shrink-0 text-coral-text" />
      </button>
    </template>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederDetail, BreederDog } from '~/types/api'
import type { BreederDogsListProps } from '~/types/BreederDogsList'
import { computed, ref, watch } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederDogsListProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
  isInWideLayout: { type: Boolean, default: false },
})

const DOG_ILLUSTRATION_SIZE_IN_PIXELS: number = 48

const areAllDogsShown: Ref<boolean> = ref(false)

const shownDogs: ComputedRef<BreederDog[]> = computed((): BreederDog[] =>
  areAllDogsShown.value ? props.breeder.reproducers : BreederPresentation.listShownDogs(props.breeder),
)
const hiddenDogsCount: ComputedRef<number> = computed(
  (): number => props.breeder.reproducers.length - shownDogs.value.length,
)
const siteDogsUrl: ComputedRef<string | null> = computed((): string | null => props.breeder.site_dogs_url ?? null)
const hasSitePhotos: ComputedRef<boolean> = computed(
  (): boolean =>
    (props.breeder.chiens_de_france_site_seen_at ?? null) !== null &&
    shownDogs.value.some((dog: BreederDog): boolean => dog.photos.length > 0),
)

watch(
  (): number => props.breeder.id,
  (): void => {
    areAllDogsShown.value = false
  },
)
</script>
