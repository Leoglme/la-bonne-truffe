<template>
  <div class="flex h-dvh overflow-hidden bg-cream">
    <MainSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <main class="min-h-0 flex-1 overflow-y-auto">
        <slot />
      </main>
      <MainTabBar />
    </div>
  </div>
</template>

<script lang="ts" setup>
/** App frame: sidebar on desktop, bottom tab bar on iPad and iPhone (docs/06, « Formes et espacements »). */
</script>
