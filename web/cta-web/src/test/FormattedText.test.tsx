import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FormattedText } from '../components/FormattedText'
import { tokenizeText } from '../format'
import { hero } from './fixtures'

describe('CTA localized text rendering', () => {
  it('renders emphasis, authentic icon references, line breaks, and placeholders accessibly', () => {
    const { container } = render(<p><FormattedText value={'Deal *critical damage* with |Elt_FI.png|.\nChance {unknown}.'} hero={hero} /></p>)
    expect(screen.getByText('critical damage').tagName).toBe('STRONG')
    expect(screen.getByLabelText('Fire element')).toHaveTextContent('[Fire element]')
    expect(container.querySelector('br')).toBeInTheDocument()
    expect(screen.getByText(/unresolved: unknown/)).toBeInTheDocument()
  })

  it('keeps unresolved printf-style formats visible', () => {
    expect(tokenizeText('Value %.1f and %s', hero)).toEqual([
      { kind: 'text', value: 'Value ' }, { kind: 'unresolved_format', value: '%.1f' },
      { kind: 'text', value: ' and ' }, { kind: 'unresolved_format', value: '%s' },
    ])
  })

  it('uses the explicit missing-description fallback', () => {
    render(<p><FormattedText hero={hero} /></p>)
    expect(screen.getByText('Description unavailable.')).toBeInTheDocument()
  })
})
