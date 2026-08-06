import type { Hero } from '../models'
import { tokenizeText } from '../format'

export function FormattedText({ value, hero }: { value?: string; hero: Hero }) {
  return <>{tokenizeText(value, hero).map((token, index) => token.kind === 'line_break' ? <br key={index} /> : token.kind === 'emphasis' ? <strong key={index}>{token.value}</strong> : token.kind === 'icon' ? <span className="inline-token" aria-label={token.value} key={index}>[{token.value}]</span> : token.kind === 'unresolved_format' ? <span className="unresolved-token" key={index}>[unresolved format: {token.value}]</span> : token.value)}</>
}
