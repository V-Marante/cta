import { useEffect, useState } from 'react'
import { ASSETS_VERSION, publicAssetUrl } from '../api'

const knownJobs = new Set(['Brawler', 'Barbarian', 'Knight', 'Rogue', 'Lancer', 'Samurai', 'Ranger', 'Magician', 'Gunner', 'Support'])
const knownElements = new Set(['Fire', 'Water', 'Earth', 'Light', 'Dark'])

export function JobIcon({ job }: { job?: string }) {
  return <GameIcon label={job ?? 'Unknown job'} category="jobs" available={knownJobs.has(job ?? '')} />
}

export function ElementIcon({ element }: { element?: string }) {
  return <GameIcon label={element ?? 'Unknown element'} category="elements" available={knownElements.has(element ?? '')} />
}

function GameIcon({ label, category, available }: { label: string; category: 'jobs' | 'elements'; available: boolean }) {
  const [failed, setFailed] = useState(false)
  const slug = label.trim().toLowerCase()
  useEffect(() => setFailed(false), [category, slug])
  const source = publicAssetUrl(`/assets/ui-icons/${encodeURIComponent(ASSETS_VERSION)}/${category}/${encodeURIComponent(slug)}.png`)
  return <span className={`hero-symbol ${category === 'jobs' ? 'job-symbol' : 'element-symbol'}`} title={label} aria-label={label}>
    {available && !failed
      ? <img src={source} alt="" aria-hidden="true" loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFailed(true)} />
      : <span className="symbol-fallback">{label}</span>}
  </span>
}
