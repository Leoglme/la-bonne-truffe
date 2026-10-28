<template>
  <nav
    aria-label="Navigation principale"
    class="hidden w-[236px] shrink-0 flex-col gap-1.5 border-r border-line bg-card px-[18px] py-7 lg:flex"
  >
    <div class="px-1 pt-1.5 pb-[22px]">
      <UiAppLogo />
    </div>
    <NuxtLink
      v-for="entry in MAIN_NAVIGATION_ENTRIES"
      :key="entry.path"
      :to="entry.path"
      :aria-current="isCurrentEntry(entry) ? 'page' : undefined"
      class="flex min-h-12 items-center gap-3 rounded-[14px] px-3.5 text-base no-underline"
      :class="
        isCurrentEntry(entry)
          ? 'bg-coral-pastel font-extrabold text-coral-text hover:text-coral-text'
          : 'font-bold text-ink-secondary hover:bg-cream hover:text-ink'
      "
    >
      <UIcon :name="entry.icon" class="size-[22px]" aria-hidden="true" />
      {{ entry.label }}
    </NuxtLink>
  </nav>
</template>

<script lang="ts" setup>
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { MainNavigationEntry } from '~/constants/mainNavigation'
import { MAIN_NAVIGATION_ENTRIES } from '~/constants/mainNavigation'

const route: RouteLocationNormalizedLoaded = useRoute()

/**
 * Whether an entry leads to the current screen or to one of its sub-screens.
 *
 * @param entry - Entry to test.
 * @returns True for the active entry.
 */
function isCurrentEntry(entry: MainNavigationEntry): boolean {
  return entry.path === '/' ? route.path === '/' : route.path.startsWith(entry.path)
}
</script>
