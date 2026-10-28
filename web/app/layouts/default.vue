<template>
  <div class="flex h-dvh overflow-hidden bg-cream">
    <MainSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <main class="flex min-h-0 flex-1 flex-col overflow-y-auto">
        <slot />
      </main>
      <MainTabBar v-if="!isPushedScreen" />
    </div>
    <FollowUpDrawer />
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { computed, onMounted, onUnmounted } from 'vue'

const route: RouteLocationNormalizedLoaded = useRoute()
const { isDesktopApp }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()
const centraleCanineRelayStore: ReturnType<typeof useCentraleCanineRelayStore> = useCentraleCanineRelayStore()

const isPushedScreen: ComputedRef<boolean> = computed((): boolean => route.meta.isPushedScreen === true)

onMounted((): void => {
  if (isDesktopApp.value) {
    centraleCanineRelayStore.startWatching()
  }
})

onUnmounted((): void => {
  centraleCanineRelayStore.stopWatching()
})
</script>
