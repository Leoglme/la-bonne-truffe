/** Coat of the cocker illustration: the colours of the mockup, plus the fallback for an unknown colour. */
export type CockerCoat = 'gold' | 'noir_et_feu' | 'noir' | 'marron' | 'bleu_rouan' | 'inconnue'

/** Fill colours of the illustration for one coat, and the pastel tile it sits on. */
export type CockerCoatPalette = {
  coat: string
  ear: string
  muzzle: string
  tile: string
  label: string
}

/** Palettes from docs/06-maquette-et-design.md and design/mockup/Criteres.dc.html. */
export const COCKER_COAT_PALETTES: Readonly<Record<CockerCoat, CockerCoatPalette>> = {
  gold: { coat: '#E9B363', ear: '#CF8F3A', muzzle: '#F3CF95', tile: '#FBE7CC', label: 'Gold' },
  noir_et_feu: { coat: '#3A2F2A', ear: '#2B2420', muzzle: '#C98A4B', tile: '#E9E3F2', label: 'Noir et feu' },
  noir: { coat: '#2F2724', ear: '#1E1816', muzzle: '#4A3C34', tile: '#EAE2DA', label: 'Noir' },
  marron: { coat: '#7B5033', ear: '#5E3A22', muzzle: '#A97A55', tile: '#EAE2DA', label: 'Marron' },
  bleu_rouan: { coat: '#8B8F99', ear: '#4E525C', muzzle: '#D9DBE0', tile: '#EAE2DA', label: 'Bleu rouan' },
  inconnue: { coat: '#6B5A50', ear: '#4A3C34', muzzle: '#B59A86', tile: '#EAE2DA', label: 'Couleur à confirmer' },
}
