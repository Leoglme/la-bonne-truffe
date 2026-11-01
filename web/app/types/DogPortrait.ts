import type { CoatColor } from '~/types/api'

export type DogPortraitProps = {
  photoUrl: string | null
  color: CoatColor | null
  sizeClass: string
  illustrationSizeInPixels: number
}
