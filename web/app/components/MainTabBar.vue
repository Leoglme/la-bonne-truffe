<template>
  <nav
    aria-label="Navigation principale"
    class="grid shrink-0 grid-cols-4 border-t border-line bg-card px-3 pt-2 pb-6 md:px-6 md:pt-2.5 md:pb-[26px] lg:hidden"
  >
    <NuxtLink
      v-for="entry in MAIN_NAVIGATION_ENTRIES"
      :key="entry.path"
      :to="entry.path"
      :aria-current="isCurrentEntry(entry) ? 'page' : undefined"
      class="flex min-h-[52px] flex-col items-center justify-center gap-[3px] text-[11px] no-underline md:min-h-[60px] md:gap-1 md:text-[13px]"
      :class="
        isCurrentEntry(entry)
          ? 'font-extrabold text-coral hover:text-coral'
          : 'font-bold text-ink-label hover:text-ink-muted'
      "
    >
      <UIcon :name="entry.icon" class="size-6 md:size-[26px]" aria-hidden="true" />
      <span>{{ entry.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script lang="ts" setup>
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { MainNavigationEntry } from '~/constants/mainNavigation'
import { MAIN_NAVIGATION_ENTRIES } from '~/constants/mainNavigation'

const route: RouteLocationNormalizedLoaded = useRoute()

/**
 * Whether a tab leads to the current screen or to one of its sub-screens.
 *
 * @param entry - Tab to test.
 * @returns True for the active tab.
 */
function isCurrentEntry(entry: MainNavigationEntry): boolean {
  return entry.path === '/' ? route.path === '/' : route.path.startsWith(entry.path)
}
</script>
