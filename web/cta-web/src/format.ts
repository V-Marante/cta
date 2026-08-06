import type { Hero, Skill } from './models'

export function humanize(value: string) { return value.replaceAll('_', ' ').replace(/([a-z])([A-Z])/g, '$1 $2') }
export type TextToken = { kind: 'text' | 'emphasis' | 'icon' | 'line_break' | 'unresolved_format'; value: string }
const iconLabels: Record<string, string> = { DA: 'Dark', LI: 'Light', FI: 'Fire', EA: 'Earth', WA: 'Water' }
export function tokenizeText(value: string | undefined, hero: Hero): TextToken[] {
  const text = (value ?? 'Description unavailable.').replaceAll('{element}', hero.element ?? 'element').replaceAll('{evade}', String(hero.stats.evade ?? '?')).replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, '[unresolved: $1]')
  const pattern = /(\n|\*[^*]+\*|\|[^|]+\||%(?:\.\d+)?[sdf](?:%%)?)/g, tokens: TextToken[] = []; let start = 0
  for (const match of text.matchAll(pattern)) { if (match.index! > start) tokens.push({ kind: 'text', value: text.slice(start, match.index) }); const raw = match[0]; if (raw === '\n') tokens.push({ kind: 'line_break', value: '' }); else if (raw.startsWith('*')) tokens.push({ kind: 'emphasis', value: raw.slice(1, -1) }); else if (raw.startsWith('|')) { const asset = raw.slice(1, -1), element = asset.match(/^Elt_([A-Z]{2})\.png$/)?.[1]; tokens.push({ kind: 'icon', value: element ? `${iconLabels[element] ?? element} element` : asset === 'HE_Star.png' ? 'star' : humanize(asset.replace(/\.png$/i, '')) }) } else tokens.push({ kind: 'unresolved_format', value: raw }); start = match.index! + raw.length }
  if (start < text.length) tokens.push({ kind: 'text', value: text.slice(start) }); return tokens
}
export function skillMechanics(skill: Skill) { const values: string[] = []; for (const part of skill.components) { const facts = part.attribute_semantics ?? {}; if (facts.cooldown && facts.cooldown.status !== 'unresolved') values.push(`Cooldown ${facts.cooldown.display_value}s`); else if (part.attributes.cooldown) values.push(`Raw cooldown ${part.attributes.cooldown}`); if (facts.effectChance && facts.effectChance.status !== 'unresolved') values.push(`Effect chance ${facts.effectChance.display_value}%`); if (part.attributes.splashRad) values.push(`AoE radius ${part.attributes.splashRad} source units`); if (part.attributes.count) values.push(`${part.attributes.count} projectiles`) } return [...new Set(values)] }
