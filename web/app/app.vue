<template>
  <UApp :toaster="{ position: 'top-center' }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>

<script lang="ts" setup>
/** Root shell: Nuxt UI provider (toasts), then the page layout. The session is restored by auth.client. */
</script>
