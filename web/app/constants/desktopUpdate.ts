import type { DesktopUpdateStatus } from '~/types/DesktopUpdate'

export const DESKTOP_UPDATE_TITLES: Record<DesktopUpdateStatus, string> = {
  idle: 'Mise à jour',
  available: 'Mise à jour disponible',
  downloading: 'Téléchargement de la mise à jour',
  installed: 'Mise à jour installée',
  error: 'Échec de la mise à jour',
}

export const DESKTOP_UPDATE_DESCRIPTIONS: Record<DesktopUpdateStatus, string> = {
  idle: '',
  available: 'L’application se ferme un instant pour finir l’installation.',
  downloading: 'Ne ferme pas La Bonne Truffe pendant le téléchargement.',
  installed: 'Redémarre l’application pour passer à la nouvelle version. Ta session est conservée.',
  error: 'La nouvelle version n’a pas pu s’installer.',
}
