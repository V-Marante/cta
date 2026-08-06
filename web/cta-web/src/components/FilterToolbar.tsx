import type { Filters, HeroQuery } from '../models'

export function FilterToolbar({ filters, query, update }: { filters: Filters; query: HeroQuery; update: (value: Partial<HeroQuery>) => void }) {
  return <section className="toolbar"><label className="search">⌕<input value={query.search} onChange={e => update({ search: e.target.value })} placeholder="Search heroes…" /></label>
    <Select label="Filter by class" value={query.heroClass} empty="All classes" options={filters.classes} change={heroClass => update({ heroClass })} />
    <Select label="Filter by element" value={query.element} empty="All elements" options={filters.elements} change={element => update({ element })} />
    <Select label="Filter by rarity" value={query.rarity} empty="All rarities" options={filters.rarities} change={rarity => update({ rarity })} />
    <Select label="Filter by mobility" value={query.mobility} empty="Ground & flying" options={filters.mobilities} change={mobility => update({ mobility })} />
    <Select label="Filter by acquisition" value={query.acquisition} empty="All acquisition" options={filters.acquisitions} change={acquisition => update({ acquisition })} />
    <select value={query.attribute} onChange={e => update({ attribute: e.target.value })} aria-label="Filter by attribute"><option value="">All attributes</option>{filters.attributes.map(x => <option value={x.value} key={x.value}>{x.label}</option>)}</select>
    <label className="toggle"><input type="checkbox" checked={query.includeVariants} onChange={e => update({ includeVariants: e.target.checked })} /> Include variants/NPCs</label>
  </section>
}

function Select({ label, value, empty, options, change }: { label: string; value: string; empty: string; options: string[]; change: (value: string) => void }) {
  return <select value={value} onChange={e => change(e.target.value)} aria-label={label}><option value="">{empty}</option>{options.map(x => <option key={x}>{x}</option>)}</select>
}
