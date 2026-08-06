import { useEffect, useMemo, useState } from 'react'
import { getHeroes } from '../api'
import type { Hero } from '../models'
import { navigate } from '../navigation'
import { exportTierListPng } from '../tierListPng'
import { ErrorState, LoadingState } from './AsyncStates'
import { Portrait } from './Portrait'

export type Tier = { id: string; name: string }
type SavedList = { version: 2; title: string; tiers: Tier[]; assignments: Record<string, string> }

export const tierColors = ['#d95f59', '#4f86c6', '#d59a3a', '#5fa66a', '#8a68b8', '#cf6f9e', '#4ba7a1', '#b26a45', '#718096', '#a8a348', '#5476a8', '#b45d68', '#568c72', '#8967a2', '#9b7447']
const storageKey = 'cta.hero-tier-list.v2'
const defaultTitle = 'Crush Them All · Hero Tier List'
const initialTiers: Tier[] = [{ id: 's', name: 'S' }]

function readSaved(): SavedList {
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) ?? '') as Partial<SavedList>
    if (value.version === 2 && Array.isArray(value.tiers) && value.tiers.length && value.tiers.length <= tierColors.length && value.tiers.every(validTier)) {
      return { version: 2, title: typeof value.title === 'string' ? value.title : defaultTitle, tiers: value.tiers, assignments: validAssignments(value.assignments) ? value.assignments : {} }
    }
  } catch { /* A corrupt local draft should not prevent using the maker. */ }
  return { version: 2, title: defaultTitle, tiers: initialTiers, assignments: {} }
}

function validTier(value: unknown): value is Tier {
  if (!value || typeof value !== 'object') return false
  const tier = value as Tier
  return typeof tier.id === 'string' && typeof tier.name === 'string'
}

function validAssignments(value: unknown): value is Record<string, string> {
  return !!value && typeof value === 'object' && Object.values(value).every(item => typeof item === 'string')
}

export function TierListMaker() {
  const saved = useMemo(readSaved, [])
  const [title, setTitle] = useState(saved.title), [tiers, setTiers] = useState(saved.tiers), [assignments, setAssignments] = useState(saved.assignments)
  const [heroes, setHeroes] = useState<Hero[]>([])
  const [loading, setLoading] = useState(true), [error, setError] = useState<string>(), [attempt, setAttempt] = useState(0)
  const [exporting, setExporting] = useState(false), [exportError, setExportError] = useState<string>()

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(undefined)
    getHeroes({ search: '', heroClass: '', element: '', rarity: '', mobility: '', acquisition: '', attribute: '' }, controller.signal)
      .then(page => setHeroes([...page.items].sort((left, right) => left.name.localeCompare(right.name))))
      .catch(value => { if (value.name !== 'AbortError') setError('Could not load heroes for the tier list.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [attempt])

  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify({ version: 2, title, tiers, assignments })) }, [title, tiers, assignments])

  const place = (heroId: string, tierId?: string) => {
    if (!heroId) return
    setAssignments(current => {
      const next = { ...current }
      if (tierId) next[heroId] = tierId; else delete next[heroId]
      return next
    })
  }
  const rename = (id: string, name: string) => setTiers(current => current.map(tier => tier.id === id ? { ...tier, name } : tier))
  const addTier = () => setTiers(current => current.length >= tierColors.length ? current : [...current, { id: crypto.randomUUID(), name: `Tier ${current.length + 1}` }])
  const deleteTier = (id: string) => {
    setTiers(current => current.filter(tier => tier.id !== id))
    setAssignments(current => Object.fromEntries(Object.entries(current).filter(([, tierId]) => tierId !== id)))
  }
  const moveTier = (id: string, offset: -1 | 1) => setTiers(current => {
    const index = current.findIndex(tier => tier.id === id), target = index + offset
    if (index < 0 || target < 0 || target >= current.length) return current
    const next = [...current]; [next[index], next[target]] = [next[target], next[index]]
    return next
  })
  const reset = () => { setTitle(defaultTitle); setTiers(initialTiers); setAssignments({}) }
  const randomize = () => setAssignments(Object.fromEntries(heroes.map(hero => [hero.id, tiers[Math.floor(Math.random() * tiers.length)].id])))
  const download = async () => {
    setExporting(true); setExportError(undefined)
    try { await exportTierListPng(title.trim() || defaultTitle, tiers, tierColors, assignments, heroes) }
    catch { setExportError('Could not export this tier list. Check that portrait images are available and try again.') }
    finally { setExporting(false) }
  }
  const heroesFor = (tierId?: string) => heroes.filter(hero => tierId ? assignments[hero.id] === tierId : !tiers.some(tier => tier.id === assignments[hero.id]))

  return <main className="tier-page"><button className="back" onClick={() => navigate('/')}>← Hero library</button>
    <header className="tier-heading"><div><span className="eyebrow">Portrait ranking</span><h1 className="page-title" tabIndex={-1}>Tier List Maker</h1><label className="tier-title">Tier list title<input value={title} maxLength={80} onChange={event => setTitle(event.target.value)} /></label><p>Drag portraits into tiers. Click a ranked portrait to return it to Available. Your list stays in this browser.</p></div><div className="tier-actions"><button onClick={addTier} disabled={tiers.length >= tierColors.length}>Add tier</button>{import.meta.env.DEV && <button onClick={randomize} disabled={!heroes.length}>Random fill</button>}<button onClick={download} disabled={exporting}>{exporting ? 'Exporting…' : 'Export PNG'}</button><button onClick={reset}>Reset</button></div></header>
    {exportError && <p className="export-error" role="alert">{exportError}</p>}
    {error ? <ErrorState message={error} retry={() => setAttempt(value => value + 1)} /> : loading ? <LoadingState>Loading portraits…</LoadingState> : <div className="tier-workspace">
      <section className="tier-board" aria-label="Hero tiers">{tiers.map((tier, index) => <TierRow key={tier.id} tier={tier} color={tierColors[index]} heroes={heroesFor(tier.id)} place={place} rename={rename} remove={tiers.length > 1 ? () => deleteTier(tier.id) : undefined} moveUp={index > 0 ? () => moveTier(tier.id, -1) : undefined} moveDown={index < tiers.length - 1 ? () => moveTier(tier.id, 1) : undefined} />)}</section>
      <section className="unranked" aria-labelledby="unranked-title" onDragOver={event => event.preventDefault()} onDrop={event => place(event.dataTransfer.getData('text/plain'))}>
        <div className="unranked-heading"><h2 id="unranked-title">Available <small>{heroesFor().length}</small></h2></div>
        <PortraitPool heroes={heroesFor()} />
      </section>
    </div>}
  </main>
}

function TierRow({ tier, color, heroes, place, rename, remove, moveUp, moveDown }: { tier: Tier; color: string; heroes: Hero[]; place: (hero: string, tier?: string) => void; rename: (id: string, name: string) => void; remove?: () => void; moveUp?: () => void; moveDown?: () => void }) {
  return <section className="tier-row" aria-label={`${tier.name || 'Unnamed'} tier`} onDragOver={event => event.preventDefault()} onDrop={event => place(event.dataTransfer.getData('text/plain'), tier.id)}>
    <div className="tier-label" style={{ backgroundColor: color, color: readableText(color) }}><input aria-label="Tier name" value={tier.name} maxLength={30} onChange={event => rename(tier.id, event.target.value)} /></div>
    <PortraitPool heroes={heroes} remove={heroId => place(heroId)} />
    <div className="tier-controls"><div className="tier-order">{moveUp && <button aria-label={`Move ${tier.name || 'unnamed'} tier up`} onClick={moveUp}>↑</button>}{moveDown && <button aria-label={`Move ${tier.name || 'unnamed'} tier down`} onClick={moveDown}>↓</button>}</div>{remove && <button aria-label={`Delete ${tier.name || 'unnamed'} tier`} onClick={remove}>Delete</button>}</div>
  </section>
}

function PortraitPool({ heroes, remove }: { heroes: Hero[]; remove?: (id: string) => void }) {
  return <div className="portrait-pool">{heroes.map(hero => remove
    ? <button key={hero.id} className="tier-portrait" aria-label={`Return ${hero.name} to Available`} title={hero.name} draggable onDragStart={event => event.dataTransfer.setData('text/plain', hero.id)} onClick={() => remove(hero.id)}><Portrait hero={hero} /><span className="tier-portrait-name">{hero.name}</span></button>
    : <div key={hero.id} className="tier-portrait" title={hero.name} draggable onDragStart={event => event.dataTransfer.setData('text/plain', hero.id)}><Portrait hero={hero} /><span className="tier-portrait-name">{hero.name}</span></div>)}</div>
}

function readableText(color: string) {
  const [red, green, blue] = [1, 3, 5].map(index => Number.parseInt(color.slice(index, index + 2), 16))
  return (red * 299 + green * 587 + blue * 114) / 1000 > 145 ? '#10182b' : '#ffffff'
}
