export type UiPhotoViewerPhoto = {
  url: string
  caption: string | null
}

export type UiPhotoViewerProps = {
  open: boolean
  photos: UiPhotoViewerPhoto[]
  startIndex: number
}

export type UiPhotoViewerEmits = {
  (event: 'update:open', isOpen: boolean): void
}
