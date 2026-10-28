<template>
  <UApp :toaster="{ position: 'top-center' }">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <DesktopUpdateModal />
  </UApp>
</template>
