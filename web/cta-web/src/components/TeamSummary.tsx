import type { Hero } from '../models'
import { fourthAbilityName } from '../fourthAbility'
import { ElementIcon } from './HeroSymbols'
import { FourthAbilityTarget } from './FourthAbilityTarget'

export function TeamSummary({ heroes }: { heroes: Hero[] }) {
  const elements = count(heroes, hero => hero.element ?? 'Unknown element')
  const jobs = count(heroes, hero => hero.class ?? 'Unknown job')
  const abilities = heroes.filter(hero => hero.passive.name || hero.passive.code)
  return <>
    <aside className="team-counts"><h2>Composition</h2><SummaryGroup title="Elements" values={elements} icons /><SummaryGroup title="Jobs" values={jobs} /></aside>
    <section className="team-abilities"><h2>Fourth abilities</h2>{abilities.length ? <ul>{abilities.map(hero => <li key={hero.id}><strong>{hero.name}</strong><span>{fourthAbilityName(hero.passive)}</span><FourthAbilityTarget passive={hero.passive} /></li>)}</ul> : <p>None available for this team.</p>}</section>
  </>
}

function count(heroes: Hero[], select: (hero: Hero) => string) {
  return Object.entries(heroes.reduce<Record<string, number>>((result, hero) => { const value = select(hero); result[value] = (result[value] ?? 0) + 1; return result }, {})).sort(([left], [right]) => left.localeCompare(right))
}

function SummaryGroup({ title, values, icons = false }: { title: string; values: [string, number][]; icons?: boolean }) {
  return <section><h3>{title}</h3>{values.length ? <ul>{values.map(([label, total]) => <li key={label}>{icons ? <ElementIcon element={label} /> : <span>{label}</span>}<strong>{total}</strong></li>)}</ul> : <p>None yet.</p>}</section>
}
