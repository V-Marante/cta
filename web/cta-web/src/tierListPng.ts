import { API_URL } from './api'
import type { Hero } from './models'
import type { Tier } from './components/TierListMaker'

const width = 1400, labelWidth = 150, portraitSize = 72, nameHeight = 30, cardWidth = 78, cardHeight = portraitSize + nameHeight, gap = 7, padding = 14, titleHeight = 84

export async function exportTierListPng(title: string, tiers: Tier[], colors: string[], assignments: Record<string, string>, heroes: Hero[]) {
  const byTier = tiers.map(tier => heroes.filter(hero => assignments[hero.id] === tier.id))
  const columns = Math.floor((width - labelWidth - padding * 2) / (cardWidth + gap))
  const heights = byTier.map(items => Math.max(cardHeight + padding * 2, Math.ceil(Math.max(items.length, 1) / columns) * (cardHeight + gap) + padding * 2))
  const canvas = document.createElement('canvas')
  canvas.width = width; canvas.height = titleHeight + heights.reduce((sum, value) => sum + value, 0) + padding
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Canvas is unavailable')
  context.fillStyle = '#10182b'; context.fillRect(0, 0, canvas.width, canvas.height)
  context.fillStyle = '#f7f2dc'; context.font = '700 34px system-ui'; context.fillText(title, padding, 52, width - padding * 2)
  const rankedHeroes = heroes.filter(hero => assignments[hero.id])
  const images = await loadPortraits(rankedHeroes)
  let y = titleHeight
  tiers.forEach((tier, tierIndex) => {
    const height = heights[tierIndex]
    context.fillStyle = colors[tierIndex]; context.fillRect(0, y, labelWidth, height)
    context.fillStyle = readableText(colors[tierIndex]); context.font = '700 28px system-ui'; context.textAlign = 'center'; context.textBaseline = 'middle'
    context.fillText(tier.name || 'Unnamed', labelWidth / 2, y + height / 2, labelWidth - 20)
    context.textAlign = 'left'; context.textBaseline = 'alphabetic'
    byTier[tierIndex].forEach((hero, index) => {
      const x = labelWidth + padding + (index % columns) * (cardWidth + gap)
      const top = y + padding + Math.floor(index / columns) * (cardHeight + gap)
      const image = images.get(hero.id)
      if (image) context.drawImage(image, x + 3, top, portraitSize, portraitSize)
      else drawFallback(context, hero, x, top)
      drawNameBox(context, hero.name, x, top + portraitSize)
    })
    context.strokeStyle = '#35445e'; context.strokeRect(0, y, width, height)
    y += height
  })
  const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('PNG encoding failed')), 'image/png'))
  const url = URL.createObjectURL(blob), link = document.createElement('a')
  link.href = url; link.download = `${fileName(title)}.png`; link.click(); URL.revokeObjectURL(url)
}

function fileName(title: string) {
  return title.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 80) || 'cta-hero-tier-list'
}

async function loadPortraits(heroes: Hero[]) {
  const entries = await Promise.all(heroes.map(async hero => [hero.id, hero.portraitUrl ? await loadImage(`${API_URL}${hero.portraitUrl}`) : null] as const))
  return new Map(entries)
}

function loadImage(source: string) {
  return new Promise<HTMLImageElement | null>(resolve => {
    const image = new Image(); image.crossOrigin = 'anonymous'; image.onload = () => resolve(image); image.onerror = () => resolve(null); image.src = source
  })
}

function drawFallback(context: CanvasRenderingContext2D, hero: Hero, x: number, y: number) {
  context.fillStyle = '#26344d'; context.fillRect(x + 3, y, portraitSize, portraitSize)
  context.fillStyle = '#ffca58'; context.font = '700 12px system-ui'; context.textAlign = 'center'; context.textBaseline = 'middle'
  drawLines(context, hero.name, x + cardWidth / 2, y + portraitSize / 2, 12, 4)
  context.textAlign = 'left'; context.textBaseline = 'alphabetic'
}

function drawNameBox(context: CanvasRenderingContext2D, name: string, x: number, y: number) {
  context.fillStyle = '#26344d'; context.fillRect(x, y, cardWidth, nameHeight)
  context.fillStyle = '#f7f2dc'; context.font = '600 9px system-ui'; context.textAlign = 'center'; context.textBaseline = 'middle'
  drawLines(context, name, x + cardWidth / 2, y + nameHeight / 2, 10, 3)
  context.textAlign = 'left'; context.textBaseline = 'alphabetic'
}

function drawLines(context: CanvasRenderingContext2D, text: string, x: number, centerY: number, maxCharacters: number, maxLines: number) {
  const lines = wrapName(text, maxCharacters, maxLines), lineHeight = 10
  lines.forEach((line, index) => context.fillText(line, x, centerY + (index - (lines.length - 1) / 2) * lineHeight))
}

function wrapName(text: string, maxCharacters: number, maxLines: number) {
  const words = text.trim().split(/\s+/), lines: string[] = []
  for (const word of words) {
    const pieces = word.match(new RegExp(`.{1,${maxCharacters}}`, 'g')) ?? ['']
    for (const piece of pieces) {
      const last = lines.at(-1)
      if (last && `${last} ${piece}`.length <= maxCharacters) lines[lines.length - 1] = `${last} ${piece}`
      else lines.push(piece)
    }
  }
  if (lines.length <= maxLines) return lines
  return [...lines.slice(0, maxLines - 1), lines.slice(maxLines - 1).join(' ')]
}

function readableText(color: string) {
  const [red, green, blue] = [1, 3, 5].map(index => Number.parseInt(color.slice(index, index + 2), 16))
  return (red * 299 + green * 587 + blue * 114) / 1000 > 145 ? '#10182b' : '#ffffff'
}
