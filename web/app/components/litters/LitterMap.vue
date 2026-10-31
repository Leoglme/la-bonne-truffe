<template>
  <div ref="mapElement" role="region" aria-label="Carte des portées" class="isolate size-full" @touchstart.stop />
</template>

<script lang="ts" setup>
import type { FeatureCollection } from 'geojson'
import type { LatLngBounds, LatLngBoundsLiteral, Map as LeafletMap, Marker } from 'leaflet'
import type { AppContext, PropType, Ref, VNode } from 'vue'
import type { LitterCard } from '~/types/api'
import type {
  LitterMapCluster,
  LitterMapEmits,
  LitterMapPlace,
  LitterMapProps,
  MapTown,
  ScreenPoint,
} from '~/types/LitterMap'
import type { GeographicPoint } from '~/types/Location'
import { getCurrentInstance, h, nextTick, onBeforeUnmount, onMounted, ref, render, watch } from 'vue'
import LitterMapHomePin from '~/components/litters/LitterMapHomePin.vue'
import LitterMapPin from '~/components/litters/LitterMapPin.vue'
import { MAP_TOWNS } from '~/constants/mapTowns'
import { DepartmentOutlinesService } from '~/services/departmentOutlinesService'
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

const DEPARTMENTS_ATTRIBUTION: string = 'Contours : IGN Admin Express 2018'
const DRIVING_TIMES_ATTRIBUTION: string = 'Trajets : OSRM · © OpenStreetMap'
const DEPARTMENT_BORDER_WIDTH_IN_PIXELS: number = 1.4
const MIN_ZOOM: number = 5
const MAX_ZOOM: number = 12
const MAX_FIT_ZOOM: number = 10
const MAX_CLUSTER_ZOOM: number = 11.5
const FRANCE_BOUNDS: LatLngBoundsLiteral = [
  [40.5, -7.5],
  [52, 11],
]
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
const TOWN_LABEL_CLASS: string =
  'absolute top-0 left-0 -translate-x-1/2 -translate-y-1/2 text-[11px] leading-none font-bold whitespace-nowrap text-ink-label'
const TOWN_LABEL_Z_OFFSET: number = -1000

const mapElement: Ref<HTMLDivElement | null> = ref(null)

let leaflet: typeof import('leaflet') | null = null
let map: LeafletMap | null = null
let clusterMarkers: Marker[] = []
let clusterPinContainers: HTMLElement[] = []
let homeMarker: Marker | null = null
let homePinContainer: HTMLElement | null = null
let townMarkers: Marker[] = []
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
 * Write the towns the current zoom has room for, leaving out those a pin would hide.
 */
function drawTowns(): void {
  if (leaflet === null || map === null) {
    return
  }
  const leafletLibrary: typeof import('leaflet') = leaflet
  const leafletMap: LeafletMap = map
  for (const marker of townMarkers) {
    marker.remove()
  }
  const zoom: number = leafletMap.getZoom()
  const project: (point: GeographicPoint) => ScreenPoint = (point: GeographicPoint): ScreenPoint =>
    leafletMap.latLngToLayerPoint([point.latitude, point.longitude])
  const pinPoints: ScreenPoint[] = clusterMarkers.map((marker: Marker): ScreenPoint =>
    leafletMap.latLngToLayerPoint(marker.getLatLng()),
  )

  if (props.homePosition !== null) {
    pinPoints.push(project(props.homePosition))
  }
  const shownTowns: MapTown[] = MAP_TOWNS.filter(
    (town: MapTown): boolean =>
      zoom >= town.minimumZoom && LitterMapPlaces.isTownLabelClearOfPins(project(town.point), pinPoints),
  )
  townMarkers = shownTowns.map((town: MapTown): Marker => {
    const label: HTMLSpanElement = document.createElement('span')
    label.className = TOWN_LABEL_CLASS
    label.textContent = town.name
    return leafletLibrary
      .marker([town.point.latitude, town.point.longitude], {
        icon: leafletLibrary.divIcon({ className: '', html: label, iconSize: [0, 0] }),
        interactive: false,
        keyboard: false,
        zIndexOffset: TOWN_LABEL_Z_OFFSET,
      })
      .addTo(leafletMap)
  })
}

/**
 * Draw the departments in the colours of the app, under the towns and the pins.
 *
 * @param outlines - Their outlines, null when they could not be read.
 */
function drawDepartments(outlines: FeatureCollection | null): void {
  if (leaflet === null || map === null || outlines === null) {
    return
  }
  const styles: CSSStyleDeclaration = getComputedStyle(map.getContainer())
  leaflet
    .geoJSON(outlines, {
      style: {
        color: styles.getPropertyValue('--color-card').trim(),
        weight: DEPARTMENT_BORDER_WIDTH_IN_PIXELS,
        fillColor: styles.getPropertyValue('--color-map-land').trim(),
        fillOpacity: 1,
      },
      interactive: false,
      attribution: DEPARTMENTS_ATTRIBUTION,
    })
    .addTo(map)
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
    drawTowns()
  },
)
watch(
  (): GeographicPoint | null => props.homePosition,
  (homePosition: GeographicPoint | null, previousHomePosition: GeographicPoint | null): void => {
    drawHome()
    drawTowns()
    if (homePosition !== null && previousHomePosition === null) {
      fitToOpeningView()
    }
  },
)

onMounted(async (): Promise<void> => {
  const departmentOutlinesRequest: Promise<FeatureCollection | null> = DepartmentOutlinesService.load()
  leaflet = await import('leaflet')
  if (mapElement.value === null) {
    return
  }
  map = leaflet.map(mapElement.value, {
    preferCanvas: true,
    zoomControl: false,
    zoomSnap: ZOOM_SNAP,
    minZoom: MIN_ZOOM,
    maxZoom: MAX_ZOOM,
    maxBounds: FRANCE_BOUNDS,
    maxBoundsViscosity: 1,
  })
  map.attributionControl.setPrefix(false)
  map.attributionControl.addAttribution(DRIVING_TIMES_ATTRIBUTION)
  map.on('click', (): void => emit('update:selectedLitterIds', []))
  map.on('zoomend', (): void => {
    drawClusters()
    drawTowns()
  })
  await nextTick()
  map.invalidateSize()
  fitToOpeningView()
  drawClusters()
  drawTowns()
  drawHome()
  drawDepartments(await departmentOutlinesRequest)
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
