import { useCallback, useEffect, useState } from 'react'
import { getHero } from '../api'
import { formatText, humanize, skillMechanics } from '../format'
import type { HeroDetailModel } from '../models'
import { navigate } from '../navigation'
import { ErrorState, LoadingState } from './AsyncStates'
import { Portrait } from './Portrait'

export function HeroDetail({ id }: { id: string }) {
  const [data, setData] = useState<HeroDetailModel | null>(null), [error, setError] = useState<string>(), [attempt, setAttempt] = useState(0)
  const retry = useCallback(() => setAttempt(value => value + 1), [])
  useEffect(() => { const controller = new AbortController(); setError(undefined); getHero(id, controller.signal).then(setData).catch(error => { if (error.name !== 'AbortError') setError(error.message.includes('404') ? 'Hero not found.' : 'Could not load this hero.') }); return () => controller.abort() }, [id, attempt])
  if (error) return <main><button className="back" onClick={() => navigate('/')}>← Hero library</button><ErrorState message={error} retry={retry} /></main>
  if (!data) return <main><LoadingState>Loading hero…</LoadingState></main>
  const { hero, skills } = data, passiveName = String(hero.passive.name ?? humanize(String(hero.passive.code ?? 'Passive unavailable'))), currentAcquisition = hero.acquisition.filter(source => source.current)
  return <main><button className="back" onClick={() => navigate('/')}>← Hero library</button><section className="hero-head"><Portrait hero={hero} large /><div><span className="eyebrow">{hero.element ?? 'Unknown element'} {hero.class ?? 'Hero'}</span><h1>{hero.name}</h1><p>{hero.damageType ?? 'Unknown damage type'} · {humanize(hero.mobility ?? 'Unknown')}</p></div></section>
    <section className="profile"><Field label="Job" value={hero.class} /><Field label="Element" value={hero.element} /><Field label="Mobility" value={humanize(hero.mobility ?? 'Unknown')} /><Field label="Sex" value={hero.sex === 'f' ? 'Female' : hero.sex === 'm' ? 'Male' : 'Unknown'} /><Field label="Source base stars" value={hero.progression.base_stars} title="Raw Heroes.csv BaseStars value; exact player-facing semantics are not confirmed." /><Field label="Source max stars" value={hero.progression.max_stars} title="Raw Heroes.csv MaxStars value; all currently playable records use 8." /><Field label="Rarity" value={hero.progression.rarity_name ?? hero.progression.rarity} /></section>
    <h2 className="section-title">Medal acquisition</h2><section className="availability">{currentAcquisition.length ? currentAcquisition.map(source => <span className="available" key={source.id}>✓ {source.name}</span>) : <span className="unavailable">Source unavailable in extracted configuration</span>}</section>
    <h2 className="section-title">Passives / Attributes</h2><section className="skills traits">{hero.traits.length ? hero.traits.map(trait => <article key={trait.code}><span>Innate attribute</span><h3>{trait.name}</h3><p>{formatText(trait.description, hero)}</p></article>) : <p className="state">No innate attributes found.</p>}</section>
    <h2 className="section-title">Masteries</h2><section className="stats">{Object.entries(hero.stats).filter(([, value]) => value !== null).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{value}</strong></div>)}</section>
    <h2 className="section-title">Spells / Ultimates</h2><section className="skills">{skills.length ? skills.map((skill, index) => <article key={skill.id}><span>{['First · Basic', 'Second · Special', 'Third · Ultimate'][index] ?? skill.type ?? 'Ability'}</span><h3>{skill.name || humanize(skill.id)}</h3><p>{formatText(skill.description, hero)}</p><div className="mechanics">{skillMechanics(skill).map(value => <small key={value}>{value}</small>)}</div>{skill.components.length > 0 && <details><summary>Source mechanics</summary>{skill.components.map((part, i) => <div className="source-part" key={`${part.kind}-${i}`}><b>{humanize(part.kind)}</b>{Object.entries(part.attributes).map(([key, value]) => <small key={key}>{humanize(key)}: {value}</small>)}</div>)}</details>}</article>) : <p className="state">No resolved skills available.</p>}
      {hero.passive.code && <article><span>Fourth · Passive</span><h3>{passiveName}</h3><p>{hero.passive.description ?? `${hero.passive.target ? `Affects ${String(hero.passive.target).toLowerCase()}.` : ''} ${hero.passive.source_value != null ? `Source value: ${hero.passive.source_value}.` : ''}`}</p></article>}</section>
  </main>
}

function Field({ label, value, title }: { label: string; value: unknown; title?: string }) { return <div title={title}><span>{label}</span><strong>{String(value ?? '—')}</strong></div> }
