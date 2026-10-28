/** One shape of an icon drawn in the mockup (design/mockup/*.dc.html), in its 24 × 24 viewBox. */
export type MockupIconShape =
  | { element: 'path'; d: string; fill?: string }
  | { element: 'circle'; cx: number; cy: number; r: number; fill?: string }
  | { element: 'line'; x1: number; y1: number; x2: number; y2: number }
  | { element: 'ellipse'; cx: number; cy: number; rx: number; ry: number; fill?: string; opacity?: number }

/** An icon: its shapes, and whether it is a filled glyph or a stroked one. */
export type MockupIconDefinition = {
  isFilled: boolean
  shapes: readonly MockupIconShape[]
}

export type MockupIconName =
  | 'paw'
  | 'paw-filled'
  | 'heart'
  | 'heart-filled'
  | 'sliders'
  | 'gear'
  | 'rss'
  | 'bell'
  | 'check'
  | 'chevron-left'
  | 'chevron-right'
  | 'pin'
  | 'external-link'
  | 'phone'
  | 'truffle'

const HEART_PATH: string =
  'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z'

/** The icons of the mockup, copied shape for shape so the screens match it to the pixel. */
export const MOCKUP_ICONS: Readonly<Record<MockupIconName, MockupIconDefinition>> = {
  paw: {
    isFilled: false,
    shapes: [
      { element: 'circle', cx: 8.5, cy: 5.5, r: 2 },
      { element: 'circle', cx: 15.5, cy: 5.5, r: 2 },
      { element: 'circle', cx: 4.5, cy: 11, r: 2 },
      { element: 'circle', cx: 19.5, cy: 11, r: 2 },
      {
        element: 'path',
        d: 'M12 11.5c-3.2 0-6 3-6 6a3 3 0 0 0 3 3c1 0 2-.6 3-.6s2 .6 3 .6a3 3 0 0 0 3-3c0-3-2.8-6-6-6z',
      },
    ],
  },
  'paw-filled': {
    isFilled: true,
    shapes: [
      { element: 'circle', cx: 8.5, cy: 5.5, r: 2.4 },
      { element: 'circle', cx: 15.5, cy: 5.5, r: 2.4 },
      { element: 'circle', cx: 4.3, cy: 11, r: 2.3 },
      { element: 'circle', cx: 19.7, cy: 11, r: 2.3 },
      {
        element: 'path',
        d: 'M12 11c-3.6 0-6.6 3.2-6.6 6.4A3.3 3.3 0 0 0 8.7 20.7c1.1 0 2.2-.7 3.3-.7s2.2.7 3.3.7a3.3 3.3 0 0 0 3.3-3.3C18.6 14.2 15.6 11 12 11z',
      },
    ],
  },
  heart: { isFilled: false, shapes: [{ element: 'path', d: HEART_PATH }] },
  'heart-filled': { isFilled: true, shapes: [{ element: 'path', d: HEART_PATH }] },
  sliders: {
    isFilled: false,
    shapes: [
      { element: 'line', x1: 4, y1: 7, x2: 20, y2: 7 },
      { element: 'line', x1: 4, y1: 12, x2: 20, y2: 12 },
      { element: 'line', x1: 4, y1: 17, x2: 20, y2: 17 },
      { element: 'circle', cx: 9, cy: 7, r: 2.2, fill: '#FFFFFF' },
      { element: 'circle', cx: 15, cy: 12, r: 2.2, fill: '#FFFFFF' },
      { element: 'circle', cx: 7, cy: 17, r: 2.2, fill: '#FFFFFF' },
    ],
  },
  gear: {
    isFilled: false,
    shapes: [
      { element: 'circle', cx: 12, cy: 12, r: 3 },
      {
        element: 'path',
        d: 'M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
      },
    ],
  },
  rss: {
    isFilled: false,
    shapes: [
      { element: 'path', d: 'M4 11a9 9 0 0 1 9 9' },
      { element: 'path', d: 'M4 4a16 16 0 0 1 16 16' },
      { element: 'circle', cx: 5, cy: 19, r: 1.2, fill: 'currentColor' },
    ],
  },
  bell: {
    isFilled: false,
    shapes: [
      { element: 'path', d: 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9' },
      { element: 'path', d: 'M13.73 21a2 2 0 0 1-3.46 0' },
    ],
  },
  check: { isFilled: false, shapes: [{ element: 'path', d: 'M20 6L9 17l-5-5' }] },
  'chevron-left': { isFilled: false, shapes: [{ element: 'path', d: 'M15 18l-6-6 6-6' }] },
  'chevron-right': { isFilled: false, shapes: [{ element: 'path', d: 'M9 6l6 6-6 6' }] },
  pin: {
    isFilled: false,
    shapes: [
      { element: 'path', d: 'M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z' },
      { element: 'circle', cx: 12, cy: 10, r: 3 },
    ],
  },
  'external-link': {
    isFilled: false,
    shapes: [
      { element: 'path', d: 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6' },
      { element: 'path', d: 'M15 3h6v6' },
      { element: 'path', d: 'M10 14L21 3' },
    ],
  },
  phone: {
    isFilled: false,
    shapes: [
      {
        element: 'path',
        d: 'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z',
      },
    ],
  },
  truffle: {
    isFilled: true,
    shapes: [
      { element: 'path', d: 'M4 9c0-3.5 3.6-6 8-6s8 2.5 8 6c0 4.5-4.5 9-8 11C8.5 18 4 13.5 4 9z' },
      { element: 'ellipse', cx: 9.2, cy: 9.2, rx: 1.6, ry: 2.1, fill: '#FBF6EE' },
      { element: 'ellipse', cx: 14.8, cy: 9.2, rx: 1.6, ry: 2.1, fill: '#FBF6EE' },
    ],
  },
}
