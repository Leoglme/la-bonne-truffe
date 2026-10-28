export type CustomIconName =
  'paw' | 'paw-filled' | 'heart' | 'heart-filled' | 'sliders' | 'gear' | 'rss' | 'bell' | 'pin' | 'phone' | 'truffle'

export type CustomIconPath = {
  element: 'path'
  d: string
}

export type CustomIconCircle = {
  element: 'circle'
  cx: number
  cy: number
  r: number
  fillClass?: string
}

export type CustomIconLine = {
  element: 'line'
  x1: number
  y1: number
  x2: number
  y2: number
}

export type CustomIconEllipse = {
  element: 'ellipse'
  cx: number
  cy: number
  rx: number
  ry: number
  fillClass?: string
}

export type CustomIconShape = CustomIconPath | CustomIconCircle | CustomIconLine | CustomIconEllipse

export type CustomIconDefinition = {
  isFilled: boolean
  shapes: CustomIconShape[]
}

export type UiCustomIconProps = {
  name: CustomIconName
  sizeInPixels: number
  strokeWidth: number
}
