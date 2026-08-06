import { useEffect, useState } from 'react'
import { HeroDetail } from './components/HeroDetail'
import { HeroRoster } from './components/HeroRoster'

export function App() {
  const [path, setPath] = useState(location.pathname)
  useEffect(() => { const handler = () => setPath(location.pathname); addEventListener('popstate', handler); return () => removeEventListener('popstate', handler) }, [])
  const match = path.match(/^\/heroes\/(.+)$/)
  return match ? <HeroDetail id={decodeURIComponent(match[1])} /> : <HeroRoster />
}
