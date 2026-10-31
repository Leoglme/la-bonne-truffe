<template>
  <div
    ref="mapElement"
    role="region"
    aria-label="Carte des portées"
    class="isolate size-full"
    @touchstart.stop
    @touchmove.stop
    @touchend.stop
    @touchcancel.stop
  />
</template>

<script lang="ts" setup>
import type { LatLngBounds, Map as LeafletMap, Marker } from 'leaflet'
import type { AppContext, PropType, Ref, VNode } from 'vue'
import type { LitterCard } from '~/types/api'
import type { LitterMapCluster, LitterMapEmits, LitterMapPlace, LitterMapProps, ScreenPoint } from '~/types/LitterMap'
import type { GeographicPoint } from '~/types/Location'
import { getCurrentInstance, h, nextTick, onBeforeUnmount, onMounted, ref, render, watch } from 'vue'
import LitterMapHomePin from '~/components/litters/LitterMapHomePin.vue'
import LitterMapPin from '~/components/litters/LitterMapPin.vue'
import { LitterMapPlaces, MAP_PIN_BOX_WIDTH_IN_PIXELS } from '~/utils/litterMapPlaces'

const props: LitterMapProps = defineProps({
  litters: { type: Array as PropType<LitterCard[]>, required: true },
  homePosition: { type: Object as PropType<GeographicPoint | null>, default: null },
  selectedLitterIds: { type: Array as PropType<number[]>, required: true },
})

const emit: LitterMapEmits = defineEmits<{
  (event: 'update:selectedLitterIds', litterIds: number[]): void
}>()

const pinAppContext: AppContext | null = getCurrentInstance()?.appContext ?? null

const TILE_URL: string = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION: string = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
const MAX_ZOOM: number = 18
const MAX_FIT_ZOOM: number = 11
const MAX_CLUSTER_ZOOM: number = 14
const ZOOM_SNAP: number = 0.25
const FIT_PADDING_TOP_LEFT: [number, number] = [56, 104]
const FIT_PADDING_BOTTOM_RIGHT: [number, number] = [56, 64]
const SELECTED_PIN_Z_OFFSET: number = 1000
const CARD_AREA_SHARE: number = 0.5
const BRITTANY_CENTER: GeographicPoint = { latitude: 48, longitude: -2 }
const EMPTY_MAP_ZOOM: number = 7
const CLOSEST_PLACES_AROUND_HOME: number = 6
const MARKER_CLASS: string = 'group outline-none'
const PIN_CONTAINER_CLASS: string = 'absolute top-0 left-0 -translate-x-1/2 -translate-y-1/2'

const mapElement: Ref<HTMLDivElement | null> = ref(null)

let leaflet: typeof import('leaflet') | null = null
let map: LeafletMap | null = null
let clusterMarkers: Marker[] = []
let clusterPinContainers: HTMLElement[] = []
let homeMarker: Marker | null = null
let homePinContainer: HTMLElement | null = null
let openedLitterIdsKey: string | null = null

/**
 * Render a pin component into an element Leaflet can place, inside the app so its components and icons work.
 *
 * @param vnode - The pin to render.
 * @returns The element holding it.
 */
function mountPin(vnode: VNode): HTMLElement {
  const container: HTMLDivElement = document.createElement('div')
  container.className = PIN_CONTAINER_CLASS
  vnode.appContext = pinAppContext
  render(vnode, container)
  return container
}

/**
 * Unmount pins rendered by {@link mountPin}.
 *
 * @param containers - Their elements.
 */
function unmountPins(containers: HTMLElement[]): void {
  for (const container of containers) {
    render(null, container)
  }
}

/**
 * The litters a view was opened on, to tell a new filter from a refresh of the same litters.
 *
 * @param litters - The litters.
 * @returns Their ids, sorted and joined.
 */
function buildLitterIdsKey(litters: LitterCard[]): string {
  return litters
    .map((litter: LitterCard): number => litter.id)
    .sort((first: number, second: number): number => first - second)
    .join(',')
}

/**
 * Gather the places that would overlap at the current zoom and put one pin per cluster, the selected one outlined.
 */
function drawClusters(): void {
  if (leaflet === null || map === null) {
    return
  }
  const leafletLibrary: typeof import('leaflet') = leaflet
  const leafletMap: LeafletMap = map
  for (const marker of clusterMarkers) {
    marker.remove()
  }
  unmountPins(clusterPinContainers)
  clusterPinContainers = []
  const clusters: LitterMapCluster[] = LitterMapPlaces.cluster(
    LitterMapPlaces.groupByPosition(props.litters),
    (point: GeographicPoint): ScreenPoint => leafletMap.latLngToLayerPoint([point.latitude, point.longitude]),
  )
  clusterMarkers = clusters.map((cluster: LitterMapCluster): Marker => {
    const isSelected: boolean = cluster.litters.some((litter: LitterCard): boolean =>
      props.selectedLitterIds.includes(litter.id),
    )
    const pinContainer: HTMLElement = mountPin(h(LitterMapPin, { litters: cluster.litters, isSelected }))
    clusterPinContainers.push(pinContainer)
    return leafletLibrary
      .marker([cluster.point.latitude, cluster.point.longitude], {
        icon: leafletLibrary.divIcon({ className: MARKER_CLASS, html: pinContainer, iconSize: [0, 0] }),
        keyboard: true,
        title: LitterMapPlaces.buildPinLabel(cluster.litters),
        zIndexOffset: isSelected ? SELECTED_PIN_Z_OFFSET : 0,
      })
      .on('click', (): void => openCluster(cluster))
      .addTo(leafletMap)
  })
}

/**
 * Put the house of the device where it is, or take it away while the position is unknown.
 */
function drawHome(): void {
  if (leaflet === null || map === null) {
    return
  }
  homeMarker?.remove()
  homeMarker = null
  if (homePinContainer !== null) {
    unmountPins([homePinContainer])
    homePinContainer = null
  }
  if (props.homePosition === null) {
    return
  }
  homePinContainer = mountPin(h(LitterMapHomePin))
  homeMarker = leaflet
    .marker([props.homePosition.latitude, props.homePosition.longitude], {
      icon: leaflet.divIcon({ className: MARKER_CLASS, html: homePinContainer, iconSize: [0, 0] }),
      interactive: false,
      keyboard: false,
    })
    .addTo(map)
}

/**
 * Bounds around points, for the map to show them all.
 *
 * @param points - The points; none gives null.
 * @returns Their bounds, or null.
 */
function boundsOf(points: GeographicPoint[]): LatLngBounds | null {
  if (leaflet === null || points.length === 0) {
    return null
  }
  return leaflet.latLngBounds(
    points.map((point: GeographicPoint): [number, number] => [point.latitude, point.longitude]),
  )
}

/**
 * Open on the house and its closest litters, every litter while the house is unknown, Brittany when nothing is known.
 */
function fitToOpeningView(): void {
  if (map === null) {
    return
  }
  openedLitterIdsKey = buildLitterIdsKey(props.litters)
  const bounds: LatLngBounds | null = boundsOf(
    LitterMapPlaces.pointsToOpenOn(
      LitterMapPlaces.groupByPosition(props.litters),
      props.homePosition,
      CLOSEST_PLACES_AROUND_HOME,
    ),
  )

  if (bounds === null) {
    map.setView([BRITTANY_CENTER.latitude, BRITTANY_CENTER.longitude], EMPTY_MAP_ZOOM, { animate: false })
    return
  }
  map.fitBounds(bounds, {
    paddingTopLeft: FIT_PADDING_TOP_LEFT,
    paddingBottomRight: FIT_PADDING_BOTTOM_RIGHT,
    maxZoom: MAX_FIT_ZOOM,
    animate: false,
  })
}

/**
 * A tap on a pin: zoom in on a cluster that can still split, else open its litters under the map.
 *
 * @param cluster - The cluster tapped.
 */
function openCluster(cluster: LitterMapCluster): void {
  if (map === null) {
    return
  }
  const bounds: LatLngBounds | null = boundsOf(
    cluster.places.map((place: LitterMapPlace): GeographicPoint => place.point),
  )

  if (cluster.places.length > 1 && bounds !== null && map.getZoom() < MAX_CLUSTER_ZOOM) {
    emit('update:selectedLitterIds', [])
    map.flyToBounds(bounds, {
      padding: [MAP_PIN_BOX_WIDTH_IN_PIXELS, MAP_PIN_BOX_WIDTH_IN_PIXELS],
      maxZoom: MAX_CLUSTER_ZOOM,
    })
    return
  }
  emit(
    'update:selectedLitterIds',
    cluster.litters.map((litter: LitterCard): number => litter.id),
  )
  map.panInside([cluster.point.latitude, cluster.point.longitude], {
    paddingTopLeft: FIT_PADDING_TOP_LEFT,
    paddingBottomRight: [FIT_PADDING_BOTTOM_RIGHT[0], Math.round(map.getSize().y * CARD_AREA_SHARE)],
  })
}

watch(
  (): number[] => props.selectedLitterIds,
  (): void => drawClusters(),
)
watch(
  (): LitterCard[] => props.litters,
  (): void => {
    if (buildLitterIdsKey(props.litters) !== openedLitterIdsKey) {
      fitToOpeningView()
    }
    drawClusters()
  },
)
watch(
  (): GeographicPoint | null => props.homePosition,
  (homePosition: GeographicPoint | null, previousHomePosition: GeographicPoint | null): void => {
    drawHome()
    if (homePosition !== null && previousHomePosition === null) {
      fitToOpeningView()
    }
  },
)

onMounted(async (): Promise<void> => {
  leaflet = await import('leaflet')
  if (mapElement.value === null) {
    return
  }
  map = leaflet.map(mapElement.value, { zoomControl: false, zoomSnap: ZOOM_SNAP })
  map.attributionControl.setPrefix(false)
  leaflet.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: MAX_ZOOM, detectRetina: true }).addTo(map)
  map.on('click', (): void => emit('update:selectedLitterIds', []))
  map.on('zoomend', (): void => drawClusters())
  await nextTick()
  map.invalidateSize()
  fitToOpeningView()
  drawClusters()
  drawHome()
})

onBeforeUnmount((): void => {
  unmountPins(clusterPinContainers)
  if (homePinContainer !== null) {
    unmountPins([homePinContainer])
  }
  map?.remove()
  map = null
})
</script>
