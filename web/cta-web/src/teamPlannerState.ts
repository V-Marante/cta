import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { Hero } from './models'

export const TEAM_SIZE = 10
export const TEAM_STORAGE_KEY = 'cta.team-planner.v1'
export type TeamSlots = Array<string | null>

const emptyTeam = (): TeamSlots => Array.from({ length: TEAM_SIZE }, () => null)

export function readStoredTeam(storage: Pick<Storage, 'getItem'> = localStorage): TeamSlots {
  try {
    const value: unknown = JSON.parse(storage.getItem(TEAM_STORAGE_KEY) ?? 'null')
    if (!Array.isArray(value)) return emptyTeam()
    const seen = new Set<string>()
    return emptyTeam().map((_, index) => {
      const id = value[index]
      if (typeof id !== 'string' || !id || seen.has(id)) return null
      seen.add(id)
      return id
    })
  } catch { return emptyTeam() }
}

export function reconcileTeam(slots: TeamSlots, heroes: Hero[]): TeamSlots {
  const valid = new Set(heroes.map(hero => hero.id))
  const seen = new Set<string>()
  return emptyTeam().map((_, index) => {
    const id = slots[index]
    if (!id || !valid.has(id) || seen.has(id)) return null
    seen.add(id)
    return id
  })
}

export function addHero(slots: TeamSlots, heroId: string, destination?: number): TeamSlots {
  if (slots.includes(heroId)) return slots
  const index = destination ?? slots.findIndex(id => id === null)
  if (index < 0 || index >= TEAM_SIZE) return slots
  return slots.map((id, slot) => slot === index ? heroId : id)
}

export function removeHero(slots: TeamSlots, index: number): TeamSlots {
  return slots.map((id, slot) => slot === index ? null : id)
}

export function moveHero(slots: TeamSlots, from: number, to: number): TeamSlots {
  if (from === to || from < 0 || to < 0 || from >= TEAM_SIZE || to >= TEAM_SIZE || !slots[from]) return slots
  const next = [...slots]
  ;[next[from], next[to]] = [next[to], next[from]]
  return next
}

export function useTeamPlanner(heroes: Hero[]) {
  const [slots, setSlots] = useState<TeamSlots>(() => readStoredTeam())
  const [restored, setRestored] = useState(false)
  const skipPersist = useRef(false)
  useEffect(() => {
    if (!heroes.length) return
    setSlots(current => reconcileTeam(current, heroes))
    setRestored(true)
  }, [heroes])
  useEffect(() => {
    if (skipPersist.current) { skipPersist.current = false; return }
    if (restored) localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(slots))
  }, [slots, restored])
  const add = useCallback((id: string, destination?: number) => setSlots(current => addHero(current, id, destination)), [])
  const remove = useCallback((index: number) => setSlots(current => removeHero(current, index)), [])
  const move = useCallback((from: number, to: number) => setSlots(current => moveHero(current, from, to)), [])
  const clear = useCallback(() => { skipPersist.current = true; setSlots(emptyTeam()); localStorage.removeItem(TEAM_STORAGE_KEY) }, [])
  const selected = useMemo(() => new Set(slots.filter((id): id is string => id !== null)), [slots])
  return { slots, selected, add, remove, move, clear }
}
