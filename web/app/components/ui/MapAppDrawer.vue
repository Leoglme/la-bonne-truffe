<template>
  <UDrawer
    :open="props.open"
    title="Voir sur la carte"
    :description="props.destination.placeName"
    :ui="{
      content: 'rounded-t-3xl bg-card md:mx-auto md:w-full md:max-w-md',
      container: 'gap-4 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <ul class="m-0 flex list-none flex-col gap-2.5 p-0">
          <li v-for="link in links" :key="link.key">
            <a
              :href="link.href"
              target="_blank"
              rel="noopener"
              class="flex min-h-[64px] items-center gap-3.5 rounded-2xl bg-cream px-3.5 text-ink no-underline hover:text-ink"
              @click="emit('update:open', false)"
            >
              <UiMapAppIcon :app="link.key" />
              <span class="grow text-[17px] font-bold">{{ link.label }}</span>
              <UIcon name="i-lucide-chevron-right" class="size-5 shrink-0 text-ink-muted" />
            </a>
          </li>
        </ul>
        <UButton
          color="neutral"
          variant="outline"
          size="lg"
          class="w-full justify-center"
          @click="emit('update:open', false)"
        >
          Annuler
        </UButton>
      </div>
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { MapAppLink, MapDestination } from '~/types/Location'
import type { UiMapAppDrawerEmits, UiMapAppDrawerProps } from '~/types/UiMapAppDrawer'
import { computed } from 'vue'
import { MapLinks } from '~/utils/mapLinks'

const props: UiMapAppDrawerProps = defineProps({
  open: { type: Boolean, required: true },
  destination: { type: Object as PropType<MapDestination>, required: true },
})

const emit: UiMapAppDrawerEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const links: ComputedRef<MapAppLink[]> = computed((): MapAppLink[] => MapLinks.buildDirectionsLinks(props.destination))
</script>
