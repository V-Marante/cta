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
  let page
  if (match) page = <HeroDetail id={decodeURIComponent(match[1])} />
  else if (path === '/team-planner') page = <TeamPlannerPage />
  else page = path === '/tier-list' ? <TierListMaker /> : <HeroRoster />
  return <>{page}{import.meta.env.VITE_SHOW_FAN_DISCLAIMER !== 'false' && <footer className="fan-disclaimer">This is an unofficial fan-made project and is not affiliated with or endorsed by the game’s developer or publisher. Game names, artwork, icons, and related assets belong to their respective owners.</footer>}</>
}
