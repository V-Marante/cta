import { useEffect, useState } from 'react'
import { HeroDetail } from './components/HeroDetail'
import { HeroRoster } from './components/HeroRoster'
import { TierListMaker } from './components/TierListMaker'
import { TeamPlannerPage } from './components/TeamPlannerPage'

export function App() {
  const [path, setPath] = useState(location.pathname)
  useEffect(() => { const handler = () => setPath(location.pathname); addEventListener('popstate', handler); return () => removeEventListener('popstate', handler) }, [])
  useEffect(() => { document.querySelector<HTMLElement>('h1')?.focus() }, [path])
  const match = path.match(/^\/heroes\/(.+)$/)
  if (match) return <HeroDetail id={decodeURIComponent(match[1])} />
  if (path === '/team-planner') return <TeamPlannerPage />
  return path === '/tier-list' ? <TierListMaker /> : <HeroRoster />
}
