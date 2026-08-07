import type { Hero } from '../models'
import { fourthAbilityName } from '../fourthAbility'
import { PlannerHeroCard } from './PlannerHeroCard'

export type PlannerGrouping = 'job' | 'element' | 'ability'

export function PlannerHeroLibrary({ heroes, selected, search, element, job, grouping, setSearch, setElement, setJob, setGrouping, toggle }: {
  heroes: Hero[]; selected: Set<string>; search: string; element: string; job: string; grouping: PlannerGrouping
  setSearch: (value: string) => void; setElement: (value: string) => void; setJob: (value: string) => void; setGrouping: (value: PlannerGrouping) => void; toggle: (id: string) => void
}) {
  const elements = values(heroes.map(hero => hero.element)), jobs = values(heroes.map(hero => hero.class))
  const visible = heroes.filter(hero => (!search || hero.name.toLowerCase().includes(search.toLowerCase()) || hero.id.toLowerCase().includes(search.toLowerCase())) && (!element || hero.element === element) && (!job || hero.class === job))
  const groups = [...visible.reduce<Map<string, Hero[]>>((result, hero) => {
    const label = groupLabel(hero, grouping), group = result.get(label) ?? []
    group.push(hero); result.set(label, group)
    return result
  }, new Map()).entries()].sort(([left], [right]) => left.localeCompare(right))
  return <section className="planner-library" aria-label="Available heroes"><div className="planner-library-heading"><h2>Available heroes</h2><small>{visible.length}</small></div>
    <div className="planner-filters"><label>Search heroes<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Hero name…" /></label>
      <label>Element<select value={element} onChange={event => setElement(event.target.value)}><option value="">All elements</option>{elements.map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Job (Class)<select aria-label="Job (Class)" value={job} onChange={event => setJob(event.target.value)}><option value="">All jobs (classes)</option>{jobs.map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Group by<select value={grouping} onChange={event => setGrouping(event.target.value as PlannerGrouping)}><option value="job">Job (Class)</option><option value="element">Element</option><option value="ability">Fourth ability (SP4)</option></select></label>
    </div>
    {groups.length ? <div className="planner-groups">{groups.map(([label, group]) => <section className="planner-group" key={label} aria-label={`${label} heroes`}><h3>{label} <small>{group.length}</small></h3><div className="planner-portrait-pool">{group.map(hero => <PlannerHeroCard key={hero.id} hero={hero} selected={selected.has(hero.id)} toggle={() => toggle(hero.id)} />)}</div></section>)}</div> : <p className="state">No heroes match these filters.</p>}
  </section>
}

function values(items: Array<string | undefined>) { return [...new Set(items.filter((value): value is string => Boolean(value)))].sort() }
function groupLabel(hero: Hero, grouping: PlannerGrouping) {
  if (grouping === 'element') return hero.element ?? 'Unknown element'
  if (grouping === 'ability') return fourthAbilityName(hero.passive)
  return hero.class ?? 'Unknown job'
}
