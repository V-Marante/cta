import { beforeEach, describe, expect, it } from 'vitest'
import { addHero, moveHero, readStoredTeam, reconcileTeam, removeHero, TEAM_STORAGE_KEY } from '../teamPlannerState'
import { hero } from './fixtures'

describe('team planner state', () => {
  beforeEach(() => localStorage.clear())

  it('adds no hero twice, removes heroes, and changes order', () => {
    const empty = Array(10).fill(null)
    const added = addHero(empty, 'Ada')
    expect(addHero(added, 'Ada')).toBe(added)
    const two = addHero(added, 'Bea')
    expect(moveHero(two, 0, 1).slice(0, 2)).toEqual(['Bea', 'Ada'])
    expect(removeHero(two, 0)[0]).toBeNull()
  })

  it('restores valid storage while dropping duplicates, missing heroes, and invalid data', () => {
    localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(['Ada', 'Missing', 'Ada']))
    expect(reconcileTeam(readStoredTeam(), [hero]).slice(0, 3)).toEqual(['Ada', null, null])
    localStorage.setItem(TEAM_STORAGE_KEY, '{broken')
    expect(readStoredTeam()).toEqual(Array(10).fill(null))
  })
})
