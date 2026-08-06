import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ElementIcon, JobIcon } from '../components/HeroSymbols'

describe('hero symbols', () => {
  it.each(['Brawler', 'Barbarian', 'Knight', 'Rogue', 'Lancer', 'Samurai', 'Ranger', 'Magician', 'Gunner', 'Support'])('uses an authentic local %s job icon URL', job => {
    render(<JobIcon job={job} />)
    expect(screen.getByLabelText(job).querySelector('img')).toHaveAttribute('src', expect.stringContaining(`/ui-icons/jobs/${job.toLowerCase()}.png`))
  })
  it.each(['Fire', 'Water', 'Earth', 'Light', 'Dark'])('uses an authentic local %s element icon URL', element => {
    render(<ElementIcon element={element} />)
    expect(screen.getByLabelText(element).querySelector('img')).toHaveAttribute('src', expect.stringContaining(`/ui-icons/elements/${element.toLowerCase()}.png`))
  })
  it('falls back to visible text when an authentic icon is unavailable', () => {
    render(<JobIcon job="Ranger" />)
    fireEvent.error(screen.getByLabelText('Ranger').querySelector('img')!)
    expect(screen.getByLabelText('Ranger')).toHaveTextContent('Ranger')
  })
})
