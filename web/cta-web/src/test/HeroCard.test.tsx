import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HeroCard } from '../components/HeroCard'
import { hero } from './fixtures'

describe('HeroCard', () => {
  it('renders hero data and missing portrait fallback', () => {
    render(<HeroCard hero={hero} />)
    expect(screen.getByRole('heading', { name: 'Ada Hero' })).toBeInTheDocument()
    expect(screen.getByLabelText('Portrait unavailable')).toHaveTextContent('Ada Hero')
    expect(screen.getByLabelText('Ranger')).toBeInTheDocument()
    expect(screen.getByLabelText('Fire')).toBeInTheDocument()
  })
  it('navigates to hero detail', () => {
    render(<HeroCard hero={hero} />); fireEvent.click(screen.getByRole('button'))
    expect(location.pathname).toBe('/heroes/Ada')
  })
})
