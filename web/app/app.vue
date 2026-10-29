<template>
  <UApp :locale="fr" :toaster="{ position: 'top-center' }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <DesktopUpdateModal />
  </UApp>
</template>

<script lang="ts" setup>
import { fr } from '@nuxt/ui/locale'
</script>
