import { afterEach, describe, expect, it, vi } from 'vitest'
import { exportTierListPng } from '../tierListPng'
import { hero } from './fixtures'

afterEach(() => vi.restoreAllMocks())

describe('exportTierListPng', () => {
  it('downloads a PNG and draws a fallback when no local portrait exists', async () => {
    const context = { fillStyle: '', strokeStyle: '', font: '', textAlign: '', textBaseline: '', fillRect: vi.fn(), fillText: vi.fn(), strokeRect: vi.fn(), drawImage: vi.fn() }
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as unknown as CanvasRenderingContext2D)
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation(callback => callback(new Blob(['png'], { type: 'image/png' })))
    const createUrl = vi.fn(() => 'blob:test'), revokeUrl = vi.fn(), click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeUrl })
    await exportTierListPng('My Arena Picks', [{ id: 's', name: 'S' }], ['#d95f59'], { Ada: 's' }, [hero])
    expect(context.fillText).toHaveBeenCalledWith('My Arena Picks', 14, 52, 1372)
    expect(context.fillText).toHaveBeenCalledWith('Ada Hero', expect.any(Number), expect.any(Number))
    expect(createUrl).toHaveBeenCalledWith(expect.objectContaining({ type: 'image/png' }))
    expect(click.mock.instances[0]).toHaveAttribute('download', 'my-arena-picks.png')
    expect(click).toHaveBeenCalledOnce(); expect(revokeUrl).toHaveBeenCalledWith('blob:test')
  })
})
