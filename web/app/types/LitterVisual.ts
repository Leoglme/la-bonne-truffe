import type { LitterCard } from '~/types/api'

export type ImageLoading = 'lazy' | 'eager'

export type LitterVisualProps = {
  litter: LitterCard
  illustrationSizeInPixels: number
  photoPosition: string
  illustrationClass: string
  photoLoading: ImageLoading
}
