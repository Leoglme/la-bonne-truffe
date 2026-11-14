export type CockerCoat =
  | 'gold'
  | 'noir_et_feu'
  | 'noir'
  | 'marron'
  | 'marron_et_feu'
  | 'bleu_rouan'
  | 'orange_rouan'
  | 'marron_rouan'
  | 'tricolore'
  | 'particolore'
  | 'zibeline'
  | 'autre'
  | 'inconnue'

export type CockerCoatPalette = {
  coat: string
  ear: string
  muzzle: string
  faceOutline: string | null
  tileClass: string
  badgeClass: string
}
