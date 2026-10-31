import type { LitterCard } from '~/types/api'
import type { GeographicPoint } from '~/types/Location'

export type MapTown = {
  name: string
  point: GeographicPoint
  minimumZoom: number
}

export type ScreenPoint = {
  x: number
  y: number
}

export type LitterMapPlace = {
  point: GeographicPoint
  litters: LitterCard[]
}

export type LitterMapCluster = {
  point: GeographicPoint
  places: LitterMapPlace[]
  litters: LitterCard[]
}

export type AnchoredLitterMapCluster = {
  anchor: ScreenPoint
  cluster: LitterMapCluster
}

export type LitterMapProps = {
  litters: LitterCard[]
  homePosition: GeographicPoint | null
  selectedLitterIds: number[]
}

export type LitterMapEmits = {
  (event: 'update:selectedLitterIds', litterIds: number[]): void
}
