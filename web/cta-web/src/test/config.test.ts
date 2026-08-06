import { describe, expect, it } from 'vitest'
import { normalizeBaseUrl } from '../api'
import { portraitUrl } from '../components/Portrait'

describe('deployment configuration', () => {
  it('requires an API URL in production', () => expect(() => normalizeBaseUrl('', true)).toThrow(/VITE_API_URL/))
  it('normalizes the API URL', () => expect(normalizeBaseUrl('https://api.example.test/', true)).toBe('https://api.example.test'))
  it('uses the external asset origin when configured', () => expect(portraitUrl('/heroes/v1/a.webp', 'https://api.test', 'https://assets.test/')).toBe('https://assets.test/heroes/v1/a.webp'))
  it('falls back to the API origin', () => expect(portraitUrl('/portraits/a.png', 'https://api.test', '')).toBe('https://api.test/portraits/a.png'))
})
