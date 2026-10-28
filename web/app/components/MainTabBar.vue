<template>
  <nav
    aria-label="Navigation principale"
    class="grid shrink-0 grid-cols-4 border-t border-line bg-card px-3 pt-2 pb-6 md:px-6 md:pt-2.5 md:pb-[26px] lg:hidden"
  >
    <NuxtLink
      v-for="entry in tabEntries"
      :key="entry.path"
      :to="entry.path"
      :aria-current="MainNavigation.isEntryActive(entry, route.path) ? 'page' : undefined"
      class="flex min-h-[52px] flex-col items-center justify-center gap-[3px] text-[11px] no-underline md:min-h-[60px] md:gap-1 md:text-[13px]"
      :class="
        MainNavigation.isEntryActive(entry, route.path)
          ? 'font-extrabold text-coral hover:text-coral'
          : 'font-bold text-ink-label hover:text-ink-label'
      "
    >
      <UiCustomIcon
        :name="MainNavigation.isEntryActive(entry, route.path) ? entry.activeIcon : entry.icon"
        :size-in-pixels="26"
        :stroke-width="MainNavigation.isEntryActive(entry, route.path) ? 2.2 : 2"
        class="size-6 md:size-[26px]"
      />
      <span>{{ entry.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script lang="ts" setup>
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { MainNavigationEntry } from '~/types/MainNavigation'
import { MAIN_NAVIGATION_ENTRIES } from '~/constants/mainNavigation'
import { MainNavigation } from '~/utils/mainNavigation'

const route: RouteLocationNormalizedLoaded = useRoute()

const tabEntries: MainNavigationEntry[] = MAIN_NAVIGATION_ENTRIES.filter(
  (entry: MainNavigationEntry): boolean => entry.isInTabBar,
)
</script>
