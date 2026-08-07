import type { Hero } from '../models'

export function needsClassificationNote(hero: Hero) {
  return hero.classification !== 'collectible' || hero.classificationConfidence === 'low'
}

export function ClassificationMarker({ hero }: { hero: Hero }) {
  if (!needsClassificationNote(hero)) return null
  return <sup className="classification-marker" aria-label="Classification needs review" title="Classification needs review">*</sup>
}

export function ClassificationDisclaimer() {
  return <p className="classification-disclaimer"><sup>*</sup> Low-confidence or non-collectible source classification; shown for reference.</p>
}
