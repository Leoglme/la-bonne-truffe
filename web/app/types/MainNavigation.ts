import type { CustomIconName } from '~/types/UiCustomIcon'

export type MainNavigationEntry = {
  label: string
  path: string
  icon: CustomIconName
  activeIcon: CustomIconName
  isInTabBar: boolean
}
