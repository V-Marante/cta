import { useEffect, useMemo, useState } from 'react'
import { getHeroes } from '../api'
import type { Hero } from '../models'
import { navigate } from '../navigation'
import { useTeamPlanner } from '../teamPlannerState'
import { ErrorState, LoadingState } from './AsyncStates'
import { PlannerHeroLibrary, type PlannerGrouping } from './PlannerHeroLibrary'
import { TeamSlotGrid } from './TeamSlotGrid'
import { TeamSummary } from './TeamSummary'

const allHeroes = { search: '', heroClass: '', element: '', rarity: '', mobility: '', acquisition: '', attribute: '' }

export function TeamPlannerPage() {
  const [heroes, setHeroes] = useState<Hero[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState<string>()
  const [attempt, setAttempt] = useState(0), [search, setSearch] = useState(''), [element, setElement] = useState(''), [job, setJob] = useState(''), [grouping, setGrouping] = useState<PlannerGrouping>('job')
  const planner = useTeamPlanner(heroes)
  useEffect(() => {
    const controller = new AbortController(); let active = true
    setLoading(true); setError(undefined)
    getHeroes(allHeroes, controller.signal).then(page => { if (active) setHeroes(page.items) }).catch(reason => { if (active && reason.name !== 'AbortError') setError('Could not load heroes. Check that the API is running and try again.') }).finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [attempt])
  const byId = useMemo(() => new Map(heroes.map(hero => [hero.id, hero])), [heroes])
  const team = planner.slots.flatMap(id => id && byId.has(id) ? [byId.get(id)!] : [])
  const toggle = (id: string) => {
    const index = planner.slots.indexOf(id)
    if (index >= 0) planner.remove(index); else planner.add(id)
  }
  return <main className="team-planner"><button className="back" onClick={() => navigate('/')}>← Hero library</button><header className="planner-heading"><div><span className="eyebrow">Portrait team builder</span><h1 className="page-title" tabIndex={-1}>Team Planner</h1><p>Click a portrait to add or remove a hero.</p></div></header>
    {error ? <ErrorState message={error} retry={() => setAttempt(value => value + 1)} /> : loading ? <LoadingState /> : <>
      <div className="team-heading"><div><h2>Selected heroes</h2><p className="team-count" aria-live="polite">Team: {team.length} / 10 heroes · {team.length ? 'Valid' : 'Add at least one hero'}</p></div><button type="button" onClick={planner.clear} disabled={!team.length}>Clear team</button></div>
      <section className="team-overview" aria-label="Team summary"><TeamSlotGrid slots={planner.slots} heroes={byId} remove={planner.remove} /><TeamSummary heroes={team} /></section>
      <PlannerHeroLibrary heroes={heroes} selected={planner.selected} search={search} element={element} job={job} grouping={grouping} setSearch={setSearch} setElement={setElement} setJob={setJob} setGrouping={setGrouping} toggle={toggle} />
    </>}
  </main>
}
