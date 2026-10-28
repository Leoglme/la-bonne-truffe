/**
 * Size set of the detail pieces: `responsive` follows the iPhone then iPad measures of the detail
 * screen, `panel` the fixed measures of the desktop side panel.
 */
export type LitterDetailVariant = 'responsive' | 'panel'

export type LitterDetailPieceProps = {
  variant: LitterDetailVariant
}
