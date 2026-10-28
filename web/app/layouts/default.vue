<template>
  <div class="flex h-dvh overflow-hidden bg-cream">
    <MainSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <main class="flex min-h-0 flex-1 flex-col overflow-y-auto">
        <slot />
      </main>
      <MainTabBar v-if="!isPushedScreen" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { computed } from 'vue'

/** App frame: sidebar on desktop, bottom tab bar on iPad and iPhone except on pushed screens. */
const route: RouteLocationNormalizedLoaded = useRoute()

const isPushedScreen: ComputedRef<boolean> = computed((): boolean => route.meta.isPushedScreen === true)
</script>
