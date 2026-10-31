/** Calendar helpers in Europe/Warsaw (Playwright sets timezoneId). */

export function todayIso(): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Warsaw',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  const y = parts.find((p) => p.type === 'year')!.value
  const m = parts.find((p) => p.type === 'month')!.value
  const d = parts.find((p) => p.type === 'day')!.value
  return `${y}-${m}-${d}`
}

export function addDaysIso(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const dt = new Date(Date.UTC(y!, m! - 1, d!))
  dt.setUTCDate(dt.getUTCDate() + days)
  return dt.toISOString().slice(0, 10)
}

/** Mid-horizon stay window to avoid same-day / sold-out collisions with seed traffic. */
export function stayWindow(offsetDays = 35, nights = 2): { checkIn: string; checkOut: string } {
  const checkIn = addDaysIso(todayIso(), offsetDays)
  return { checkIn, checkOut: addDaysIso(checkIn, nights) }
}

export function monthOf(iso: string): string {
  return iso.slice(0, 7)
}
