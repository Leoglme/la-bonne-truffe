export type UiPhotoMosaicProps = {
  photos: string[]
  badgeLabel: string | null
  firstPhotoPosition: string
}

export type UiPhotoMosaicEmits = {
  (event: 'open', photoIndex: number): void
}

export type UiPhotoMosaicTile = {
  photo: string
  photoIndex: number
  ariaLabel: string
  placementClass: string
}
