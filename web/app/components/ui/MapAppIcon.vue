<template>
  <img
    :src="MAP_APP_ICON_SOURCES[props.app]"
    :alt="`Icône de ${MAP_APP_LABELS[props.app]}`"
    width="44"
    height="44"
    class="size-11 shrink-0 rounded-[10px]"
  />
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { MapAppKey } from '~/types/Location'
import type { UiMapAppIconProps } from '~/types/UiMapAppIcon'
import { MAP_APP_ICON_SOURCES, MAP_APP_LABELS } from '~/constants/mapApps'

const props: UiMapAppIconProps = defineProps({
  app: { type: String as PropType<MapAppKey>, required: true },
})
</script>
