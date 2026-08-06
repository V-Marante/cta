import { useCallback, useEffect, useState } from 'react'
import { getFilters, getHeroes } from '../api'
import type { Filters, Hero, HeroQuery } from '../models'
import { EmptyState, ErrorState, LoadingState } from './AsyncStates'
import { FilterToolbar } from './FilterToolbar'
import { HeroCard } from './HeroCard'

const emptyFilters: Filters = { classes: [], tribes: [], elements: [], damageTypes: [], rarities: [], mobilities: [], acquisitions: [], attributes: [] }
const initialQuery: HeroQuery = { search: '', heroClass: '', element: '', rarity: '', mobility: '', acquisition: '', attribute: '', includeVariants: false }

export function HeroRoster() {
  const [heroes, setHeroes] = useState<Hero[]>([]), [filters, setFilters] = useState(emptyFilters)
  const [query, setQuery] = useState(initialQuery), [loading, setLoading] = useState(true), [error, setError] = useState<string>(), [attempt, setAttempt] = useState(0)
  const retry = useCallback(() => setAttempt(value => value + 1), [])
  useEffect(() => { const controller = new AbortController(); getFilters(controller.signal).then(setFilters).catch(error => { if (error.name !== 'AbortError') setError('Could not load hero filters.') }); return () => controller.abort() }, [attempt])
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    const timer = setTimeout(() => { setLoading(true); setError(undefined); getHeroes(query, controller.signal).then(page => { if (active) setHeroes(page.items) }).catch(error => { if (active && error.name !== 'AbortError') setError('Could not load heroes. Check that the API is running and try again.') }).finally(() => { if (active) setLoading(false) }) }, 200)
    return () => { active = false; clearTimeout(timer); controller.abort() }
  }, [query, attempt])
  return <main><header><div><span className="eyebrow">Crush Them All</span><h1>Hero Library</h1><p>Explore heroes, combat stats, and skills.</p></div><div className="orb">CTA</div></header>
    <FilterToolbar filters={filters} query={query} update={value => setQuery(current => ({ ...current, ...value }))} />
    {error ? <ErrorState message={error} retry={retry} /> : loading ? <LoadingState /> : heroes.length === 0 ? <EmptyState /> : <section className="grid">{heroes.map(hero => <HeroCard hero={hero} key={hero.id} />)}</section>}
  </main>
}
