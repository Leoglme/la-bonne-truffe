import type { LitterDetail } from '~/types/api'
import type { LitterDetailVariant } from '~/types/LitterDetailVariant'

export type LitterScoreBubbleProps = {
  litter: LitterDetail
  variant: LitterDetailVariant
}
