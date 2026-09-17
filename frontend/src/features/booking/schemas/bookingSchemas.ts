import { z } from 'zod'
import { addHotelDays, isHotelDate, nightsBetween, todayHotelDate } from '@/shared/lib/hotelDates'
import type { Messages } from '@/shared/i18n/messages'
import { getMessages } from '@/shared/i18n/localeStore'

export const MAX_STAY_NIGHTS = 30
export const MAX_LEAD_DAYS = 365
export const MIN_GUESTS = 1
export const MAX_GUESTS = 10

type ValidationMessages = Messages['validation']

export function createSearchStaySchema(v: ValidationMessages = getMessages().validation) {
  return z
    .object({
      checkIn: z.string().min(1, v.checkInRequired).refine(isHotelDate, v.checkInInvalid),
      checkOut: z.string().min(1, v.checkOutRequired).refine(isHotelDate, v.checkOutInvalid),
      guests: z.number().int(v.guestsInt).min(MIN_GUESTS, v.guestsMin).max(MAX_GUESTS, v.guestsMax),
    })
    .superRefine((value, ctx) => {
      const today = todayHotelDate()
      const maxCheckIn = addHotelDays(today, MAX_LEAD_DAYS)

      if (value.checkIn < today) {
        ctx.addIssue({ code: 'custom', path: ['checkIn'], message: v.checkInPast })
      }
      if (value.checkIn > maxCheckIn) {
        ctx.addIssue({ code: 'custom', path: ['checkIn'], message: v.checkInLead })
      }

      if (!isHotelDate(value.checkIn) || !isHotelDate(value.checkOut)) {
        return
      }

      const nights = nightsBetween(value.checkIn, value.checkOut)
      if (nights < 1) {
        ctx.addIssue({ code: 'custom', path: ['checkOut'], message: v.checkOutAfter })
      } else if (nights > MAX_STAY_NIGHTS) {
        ctx.addIssue({ code: 'custom', path: ['checkOut'], message: v.stayMax })
      }
    })
}

/** Default PL schema for unit tests and static parse without React. */
export const searchStaySchema = createSearchStaySchema()

export type SearchStayValues = z.infer<ReturnType<typeof createSearchStaySchema>>

export function createGuestDetailsSchema(v: ValidationMessages = getMessages().validation) {
  return z.object({
    firstName: z.string().trim().min(1, v.firstName).max(80),
    lastName: z.string().trim().min(1, v.lastName).max(80),
    email: z.email(v.email).max(255),
    phone: z.string().trim().max(30).optional(),
    paymentAuthorized: z.boolean().refine((value) => value === true, {
      message: v.payment,
    }),
  })
}

export const guestDetailsSchema = createGuestDetailsSchema()

export type GuestDetailsValues = z.infer<ReturnType<typeof createGuestDetailsSchema>>

export function createManageLookupSchema(v: ValidationMessages = getMessages().validation) {
  return z.object({
    code: z
      .string()
      .trim()
      .min(1, v.codeRequired)
      .max(32)
      .transform((value) => value.toUpperCase()),
    email: z.email(v.email).max(255),
  })
}

export const manageLookupSchema = createManageLookupSchema()

export type ManageLookupValues = z.infer<ReturnType<typeof createManageLookupSchema>>
