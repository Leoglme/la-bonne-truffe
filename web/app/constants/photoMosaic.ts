/** The mosaic shows the first photo large and at most four beside it; the viewer shows the rest. */
export const PHOTO_MOSAIC_MAXIMUM_TILE_COUNT: number = 5

/** Where each tile sits in the three columns and two rows of the mosaic, by number of tiles. */
export const PHOTO_MOSAIC_TILE_CLASSES_BY_COUNT: Record<number, string[]> = {
  1: ['col-span-3 row-span-2 rounded-card-compact'],
  2: ['row-span-2 rounded-card-compact', 'col-span-2 row-span-2 rounded-tile'],
  3: ['row-span-2 rounded-card-compact', 'col-span-2 rounded-tile', 'col-span-2 rounded-tile'],
  4: ['row-span-2 rounded-card-compact', 'col-span-2 rounded-tile', 'rounded-tile', 'rounded-tile'],
  5: ['row-span-2 rounded-card-compact', 'rounded-tile', 'rounded-tile', 'rounded-tile', 'rounded-tile'],
}
