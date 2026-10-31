<template>
  <div class="flex h-dvh overflow-hidden bg-cream">
    <MainSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <main
        class="relative flex min-h-0 flex-1 flex-col overflow-y-auto"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
        @touchcancel="onTouchEnd"
      >
        <UiPullToRefreshIndicator
          :pull-distance-in-pixels="pullDistanceInPixels"
          :is-ready-to-refresh="isReadyToRefresh"
          :is-refreshing="isRefreshing"
        />
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
import type { UsePullToRefreshReturn } from '~/types/Composables'
import { computed, onMounted, onUnmounted } from 'vue'

const route: RouteLocationNormalizedLoaded = useRoute()
const { isDesktopApp }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()
const centraleCanineRelayStore: ReturnType<typeof useCentraleCanineRelayStore> = useCentraleCanineRelayStore()
const puppyArrivalStore: ReturnType<typeof usePuppyArrivalStore> = usePuppyArrivalStore()
const {
  pullDistanceInPixels,
  isReadyToRefresh,
  isRefreshing,
  onTouchStart,
  onTouchMove,
  onTouchEnd,
}: UsePullToRefreshReturn = usePullToRefresh()

const isPushedScreen: ComputedRef<boolean> = computed((): boolean => route.meta.isPushedScreen === true)

onMounted(async (): Promise<void> => {
  if (isDesktopApp.value) {
    centraleCanineRelayStore.startWatching()
  }
  await puppyArrivalStore.load()
})

onUnmounted((): void => {
  centraleCanineRelayStore.stopWatching()
})
</script>
