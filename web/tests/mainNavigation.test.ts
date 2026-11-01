import { describe, expect, it } from 'vitest'
import { MainNavigation } from '../app/utils/mainNavigation'

describe('MainNavigation.buildBackLabel', (): void => {
  it('names the entry of the navigation the screen belongs to', (): void => {
    expect(MainNavigation.buildBackLabel('/suivi', 'Portées')).toBe('Suivi')
    expect(MainNavigation.buildBackLabel('/', 'Éleveurs')).toBe('Portées')
    expect(MainNavigation.buildBackLabel('/eleveurs?filtre=suivis', 'Portées')).toBe('Éleveurs')
  })

  it('names the pushed screens before the entries their paths start with', (): void => {
    expect(MainNavigation.buildBackLabel('/portees/12', 'Éleveurs')).toBe('La portée')
    expect(MainNavigation.buildBackLabel('/eleveurs/7', 'Portées')).toBe('L’élevage')
    expect(MainNavigation.buildBackLabel('/eleveurs/recherche', 'Portées')).toBe('Recherche')
    expect(MainNavigation.buildBackLabel('/carte', 'Éleveurs')).toBe('Carte')
    expect(MainNavigation.buildBackLabel('/notifications', 'Portées')).toBe('Notifications')
  })

  it('falls back when the app started on the screen or came from elsewhere', (): void => {
    expect(MainNavigation.buildBackLabel(null, 'Portées')).toBe('Portées')
    expect(MainNavigation.buildBackLabel('/partage/abc', 'Éleveurs')).toBe('Éleveurs')
  })
})
