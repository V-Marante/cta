import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import './hero-detail.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:5080'
type Stats = Record<string, string | number | null>
type Trait = { code:string; name:string; description?:string }
type Acquisition = { id:string; name:string; kind:string; medalId?:string; current:boolean }
type Hero = { id:string; name:string; class?:string; tribe?:string; element?:string; damageType?:string; sex?:string; mobility?:string; portraitUrl?:string; stats:Stats; traits:Trait[]; passive:Record<string,string|number|null>; progression:Record<string,string|number|null>; availability:Record<string,boolean|null>; acquisition:Acquisition[]; classification:string; variantOf?:string }
type SkillPart = { kind:string; attributes:Record<string,string>; text?:string }
type Skill = { id:string; name:string; description?:string; type?:string; components:SkillPart[] }
type FilterOption = { value:string; label:string }
type Filters = { classes:string[]; tribes:string[]; elements:string[]; damageTypes:string[]; rarities:string[]; mobilities:string[]; acquisitions:string[]; attributes:FilterOption[] }

function Portrait({hero, large=false}:{hero:Hero; large?:boolean}) {
  const [failed, setFailed] = useState(false)
  if (!hero.portraitUrl || failed) return <div className={`portrait placeholder ${large?'large':''}`} aria-label="Portrait unavailable">{hero.name}</div>
  return <img className={`portrait ${large?'large':''}`} src={`${API}${hero.portraitUrl}`} alt={`${hero.name} portrait`} onError={()=>setFailed(true)}/>
}

function go(path:string) { history.pushState({}, '', path); dispatchEvent(new PopStateEvent('popstate')) }

function HeroList() {
  const [heroes,setHeroes]=useState<Hero[]>([]), [filters,setFilters]=useState<Filters>({classes:[],tribes:[],elements:[],damageTypes:[],rarities:[],mobilities:[],acquisitions:[],attributes:[]})
  const [query,setQuery]=useState(''), [heroClass,setClass]=useState(''), [element,setElement]=useState(''), [rarity,setRarity]=useState(''), [mobility,setMobility]=useState(''), [acquisition,setAcquisition]=useState(''), [attribute,setAttribute]=useState(''), [includeVariants,setIncludeVariants]=useState(false), [loading,setLoading]=useState(true)
  useEffect(()=>{ fetch(`${API}/api/heroes/filters`).then(r=>r.json()).then(setFilters) },[])
  useEffect(()=>{ const timer=setTimeout(()=>{ setLoading(true); const p=new URLSearchParams({pageSize:'250'}); if(query)p.set('search',query); if(heroClass)p.set('class',heroClass); if(element)p.set('element',element); if(rarity)p.set('rarity',rarity); if(mobility)p.set('mobility',mobility); if(acquisition)p.set('acquisition',acquisition); if(attribute)p.set('attribute',attribute); if(includeVariants)p.set('includeNonCollectible','true')
    fetch(`${API}/api/heroes?${p}`).then(r=>r.json()).then(x=>setHeroes(x.items)).finally(()=>setLoading(false)) },200); return()=>clearTimeout(timer) },[query,heroClass,element,rarity,mobility,acquisition,attribute,includeVariants])
  return <main><header><div><span className="eyebrow">Crush Them All</span><h1>Hero Library</h1><p>Explore heroes, combat stats, and skills.</p></div><div className="orb">CTA</div></header>
    <section className="toolbar"><label className="search">⌕<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search heroes…"/></label>
      <select value={heroClass} onChange={e=>setClass(e.target.value)} aria-label="Filter by class"><option value="">All classes</option>{filters.classes.map(x=><option key={x}>{x}</option>)}</select>
      <select value={element} onChange={e=>setElement(e.target.value)} aria-label="Filter by element"><option value="">All elements</option>{filters.elements.map(x=><option key={x}>{x}</option>)}</select>
      <select value={rarity} onChange={e=>setRarity(e.target.value)} aria-label="Filter by rarity"><option value="">All rarities</option>{filters.rarities.map(x=><option key={x}>{x}</option>)}</select>
      <select value={mobility} onChange={e=>setMobility(e.target.value)} aria-label="Filter by mobility"><option value="">Ground & flying</option>{filters.mobilities.map(x=><option key={x}>{humanize(x)}</option>)}</select>
      <select value={acquisition} onChange={e=>setAcquisition(e.target.value)} aria-label="Filter by acquisition"><option value="">All acquisition</option>{filters.acquisitions.map(x=><option key={x}>{x}</option>)}</select>
      <select value={attribute} onChange={e=>setAttribute(e.target.value)} aria-label="Filter by attribute"><option value="">All attributes</option>{filters.attributes.map(x=><option value={x.value} key={x.value}>{x.label}</option>)}</select>
      <label className="toggle"><input type="checkbox" checked={includeVariants} onChange={e=>setIncludeVariants(e.target.checked)}/> Include variants/NPCs</label></section>
    {loading?<p className="state">Loading heroes…</p>:heroes.length===0?<p className="state">No heroes match those filters.</p>:<section className="grid">{heroes.map(hero=><button className="card" key={hero.id} onClick={()=>go(`/heroes/${encodeURIComponent(hero.id)}`)}><Portrait hero={hero}/><div><h2>{hero.name}</h2><p>{hero.class??'Unknown job'} · {hero.element??'Unknown element'}</p><span>{hero.classification==='collectible'?`${hero.progression.rarity_name??'Unknown rarity'} · ${humanize(hero.mobility??'Unknown')}`:humanize(hero.classification)}</span></div></button>)}</section>}
  </main>
}

function HeroDetail({id}:{id:string}) {
  const [data,setData]=useState<{hero:Hero;skills:Skill[]}|null>(null), [missing,setMissing]=useState(false)
  useEffect(()=>{ fetch(`${API}/api/heroes/${encodeURIComponent(id)}`).then(r=>r.ok?r.json():Promise.reject()).then(setData).catch(()=>setMissing(true)) },[id])
  if(missing)return <main><button className="back" onClick={()=>go('/')}>← Hero library</button><p className="state">Hero not found.</p></main>
  if(!data)return <main><p className="state">Loading hero…</p></main>
  const {hero,skills}=data
  const passiveName = String(hero.passive.name??humanize(String(hero.passive.code??'Passive unavailable')))
  const currentAcquisition = hero.acquisition.filter(source=>source.current)
  return <main><button className="back" onClick={()=>go('/')}>← Hero library</button><section className="hero-head"><Portrait hero={hero} large/><div><span className="eyebrow">{hero.element??'Unknown element'} {hero.class??'Hero'}</span><h1>{hero.name}</h1><p>{hero.damageType??'Unknown damage type'} · {humanize(hero.mobility??'Unknown')}</p></div></section>
    <section className="profile"><div><span>Job</span><strong>{hero.class??'Unknown'}</strong></div><div><span>Element</span><strong>{hero.element??'Unknown'}</strong></div><div><span>Mobility</span><strong>{humanize(hero.mobility??'Unknown')}</strong></div><div><span>Sex</span><strong>{hero.sex==='f'?'Female':hero.sex==='m'?'Male':'Unknown'}</strong></div><div><span>Base stars</span><strong>{hero.progression.base_stars??'—'}</strong></div><div><span>Max stars</span><strong>{hero.progression.max_stars??'—'}</strong></div><div><span>Rarity</span><strong>{hero.progression.rarity_name??hero.progression.rarity??'—'}</strong></div></section>
    <h2 className="section-title">Medal acquisition</h2><section className="availability">{currentAcquisition.length?currentAcquisition.map(source=><span className="available" key={source.id}>✓ {source.name}</span>):<span className="unavailable">Source unavailable in extracted configuration</span>}</section>
    <h2 className="section-title">Passives / Attributes</h2><section className="skills traits">{hero.traits.length?hero.traits.map(trait=><article key={trait.code}><span>Innate attribute</span><h3>{trait.name}</h3><p>{formatText(trait.description,hero)}</p></article>):<p className="state">No innate attributes found.</p>}</section>
    <h2 className="section-title">Masteries</h2><section className="stats">{Object.entries(hero.stats).filter(([,v])=>v!==null).map(([k,v])=><div key={k}><span>{k.replaceAll('_',' ')}</span><strong>{v}</strong></div>)}</section>
    <h2 className="section-title">Spells / Ultimates</h2><section className="skills">{skills.length?skills.map((skill,index)=><article key={skill.id}><span>{['First · Basic','Second · Special','Third · Ultimate'][index]??skill.type??'Ability'}</span><h3>{skill.name||humanize(skill.id)}</h3><p>{formatText(skill.description,hero)}</p><div className="mechanics">{skillMechanics(skill).map(x=><small key={x}>{x}</small>)}</div>{skill.components.length>0&&<details><summary>Source mechanics</summary>{skill.components.map((part,i)=><div className="source-part" key={`${part.kind}-${i}`}><b>{humanize(part.kind)}</b>{Object.entries(part.attributes).map(([key,value])=><small key={key}>{humanize(key)}: {value}</small>)}</div>)}</details>}</article>):<p className="state">No resolved skills available.</p>}
      {hero.passive.code&&<article><span>Fourth · Passive</span><h3>{passiveName}</h3><p>{hero.passive.description??`${hero.passive.target?`Affects ${String(hero.passive.target).toLowerCase()}.`:''} ${hero.passive.source_value!=null?`Source value: ${hero.passive.source_value}.`:''}`}</p></article>}</section>
  </main>
}

function humanize(value:string){return value.replace(/([a-z])([A-Z])/g,'$1 $2')}
function formatText(value:string|undefined,hero:Hero){return (value??'Description unavailable.').replaceAll('{element}',hero.element??'element').replaceAll('{evade}',String(hero.stats.evade??'?')).replaceAll('*','')}
function skillMechanics(skill:Skill){const values:string[]=[];for(const part of skill.components){if(part.attributes.cooldown)values.push(`Cooldown ${part.attributes.cooldown}s`);if(part.attributes.splashRad)values.push(`AoE radius ${part.attributes.splashRad}`);if(part.attributes.count)values.push(`${part.attributes.count} projectiles`)}return [...new Set(values)]}

function App(){const [path,setPath]=useState(location.pathname);useEffect(()=>{const h=()=>setPath(location.pathname);addEventListener('popstate',h);return()=>removeEventListener('popstate',h)},[]);const match=path.match(/^\/heroes\/(.+)$/);return match?<HeroDetail id={decodeURIComponent(match[1])}/>:<HeroList/>}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
