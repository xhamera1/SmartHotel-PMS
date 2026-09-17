import { addDays, differenceInCalendarDays, format, isValid, parse } from 'date-fns'
import { enUS, pl } from 'date-fns/locale'
import type { AppLocale } from '@/shared/i18n/messages'
import { localeStore } from '@/shared/i18n/localeStore'

const HOTEL_DATE = 'yyyy-MM-dd'

function dateFnsLocale(locale: AppLocale) {
  return locale === 'en' ? enUS : pl
}

/** Today as YYYY-MM-DD in Europe/Warsaw (hotel business calendar). */
export function todayHotelDate(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Warsaw',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

/** Parse hotel-night ISO date without UTC midnight shift. */
export function parseHotelDate(iso: string): Date {
  return parse(iso, HOTEL_DATE, new Date())
}

export function formatHotelDate(date: Date): string {
  return format(date, HOTEL_DATE)
}

export function isHotelDate(iso: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    return false
  }
  const parsed = parseHotelDate(iso)
  return isValid(parsed) && formatHotelDate(parsed) === iso
}

export function formatHotelDateDisplay(iso: string, locale: AppLocale = localeStore.get()): string {
  const parsed = parseHotelDate(iso)
  if (!isValid(parsed)) {
    return iso
  }
  return format(parsed, 'd MMMM yyyy', { locale: dateFnsLocale(locale) })
}

export function nightsBetween(checkIn: string, checkOut: string): number {
  return differenceInCalendarDays(parseHotelDate(checkOut), parseHotelDate(checkIn))
}

export function addHotelDays(iso: string, days: number): string {
  return formatHotelDate(addDays(parseHotelDate(iso), days))
}
