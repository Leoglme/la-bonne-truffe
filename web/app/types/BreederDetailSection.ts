import type { BreederDetail } from '~/types/api'

/** Props shared by the sections of the breeder page, which the desktop panel shows tighter. */
export type BreederDetailSectionProps = {
  breeder: BreederDetail
  isInSidePanel: boolean
}
