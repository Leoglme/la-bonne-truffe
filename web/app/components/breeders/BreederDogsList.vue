<template>
  <section v-if="props.breeder.reproducers.length > 0" class="flex flex-col gap-3">
    <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Ses reproducteurs</h2>
    <ul class="m-0 flex list-none flex-col gap-2.5 p-0">
      <li
        v-for="dog in props.breeder.reproducers"
        :key="dog.id"
        class="flex items-center gap-3 rounded-[20px] bg-card px-4 py-3 shadow-card md:px-[18px] md:py-3.5"
      >
        <img
          v-if="dog.photos[0]"
          :src="dog.photos[0]"
          alt=""
          loading="lazy"
          decoding="async"
          class="size-14 shrink-0 rounded-2xl object-cover"
        />
        <span class="flex min-w-0 grow flex-col gap-0.5">
          <span class="text-[11px] font-extrabold tracking-[0.04em] text-ink-label uppercase md:text-[13px]">
            {{ BreederPresentation.buildDogRoleLabel(dog) }}
          </span>
          <component
            :is="dog.external_url ? 'a' : 'span'"
            :href="dog.external_url ?? undefined"
            :target="dog.external_url ? '_blank' : undefined"
            :rel="dog.external_url ? 'noopener' : undefined"
            class="truncate text-[15px] font-bold text-ink no-underline md:text-[17px]"
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
        <span
          v-if="dog.rating !== null"
          class="inline-flex shrink-0 rounded-full bg-chip px-2.5 py-1 text-xs font-extrabold whitespace-nowrap text-ink-secondary"
        >
          Note {{ dog.rating }} / 6
        </span>
      </li>
    </ul>
  </section>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederDogsListProps } from '~/types/BreederDogsList'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederDogsListProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})
</script>
