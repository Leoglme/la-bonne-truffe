<template>
  <nav
    aria-label="Navigation principale"
    class="hidden w-[236px] shrink-0 flex-col gap-1.5 border-r border-line bg-card px-[18px] py-7 lg:flex"
  >
    <UiAppLogo placement="sidebar" />
    <NuxtLink
      v-for="entry in MAIN_NAVIGATION_ENTRIES"
      :key="entry.path"
      :to="entry.path"
      :aria-current="isNavigationEntryActive(entry, route.path) ? 'page' : undefined"
      class="flex min-h-12 items-center gap-3 rounded-[14px] px-3.5 text-base no-underline"
      :class="
        isNavigationEntryActive(entry, route.path)
          ? 'bg-coral-pastel font-extrabold text-coral-text hover:text-coral-text'
          : 'font-bold text-ink-secondary hover:bg-cream hover:text-ink-secondary'
      "
    >
      <UiMockupIcon
        :name="isNavigationEntryActive(entry, route.path) ? entry.activeIcon : entry.icon"
        :size-in-pixels="22"
        :stroke-width="2"
      />
      {{ entry.label }}
    </NuxtLink>
    <div class="grow" />
    <div class="flex items-center gap-2.5 rounded-[14px] bg-cream px-3.5 py-3 text-[13px] text-ink-muted">
      <span
        class="size-[9px] shrink-0 rounded-full"
        :class="sourcesStore.isEveryCollectedSourceOnline ? 'bg-online' : 'bg-coral-text'"
        aria-hidden="true"
      />
      <span>{{ collectionStatusLine }}</span>
    </div>
  </nav>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { computed, onMounted } from 'vue'
import { isNavigationEntryActive, MAIN_NAVIGATION_ENTRIES } from '~/constants/mainNavigation'
import { RelativeTime } from '~/utils/relativeTime'

const route: RouteLocationNormalizedLoaded = useRoute()
const sourcesStore: ReturnType<typeof useSourcesStore> = useSourcesStore()

const collectionStatusLine: ComputedRef<string> = computed((): string => {
  if (sourcesStore.lastRunAt === null) {
    return 'Aucun relevé pour l’instant'
  }
  const onlineCount: number = sourcesStore.onlineCount
  const sourcesOnline: string = `${onlineCount} source${onlineCount > 1 ? 's' : ''} en ligne`
  return `Relevé ${RelativeTime.since(sourcesStore.lastRunAt, new Date())} · ${sourcesOnline}`
})

onMounted((): void => {
  void sourcesStore.load()
})
</script>
