import type { CockerCoat } from '~/types/CockerCoat'
import type { CustomIconName } from '~/types/UiCustomIcon'

export type SignupHighlight = {
  label: string
  circleClass: string
  coat?: CockerCoat
  iconName?: CustomIconName
}
