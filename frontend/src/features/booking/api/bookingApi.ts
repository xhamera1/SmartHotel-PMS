import { apiClient } from '@/shared/api/client'
import type { components } from '@/shared/api/schema'

export type AvailabilityResponse = components['schemas']['AvailabilityResponse']
export type ReservationResponse = components['schemas']['ReservationResponse']
export type CreateReservationRequest = components['schemas']['CreateReservationRequest']

export const bookingKeys = {
  availability: (checkIn: string, checkOut: string, guests: number) =>
    ['availability', checkIn, checkOut, guests] as const,
  reservation: (code: string, email: string) => ['reservation', code, email] as const,
}

export async function fetchAvailability(
  checkIn: string,
  checkOut: string,
  guests: number,
): Promise<AvailabilityResponse> {
  const { data } = await apiClient.get<AvailabilityResponse>('/api/v1/availability', {
    params: { checkIn, checkOut, guests },
  })
  return data
}

export async function createReservation(
  body: CreateReservationRequest,
): Promise<ReservationResponse> {
  const { data } = await apiClient.post<ReservationResponse>('/api/v1/reservations', body)
  return data
}

export async function lookupReservation(code: string, email: string): Promise<ReservationResponse> {
  const { data } = await apiClient.get<ReservationResponse>('/api/v1/reservations/lookup', {
    params: { code, email },
  })
  return data
}

export async function cancelReservation(code: string, email: string): Promise<ReservationResponse> {
  const { data } = await apiClient.post<ReservationResponse>(
    `/api/v1/reservations/${encodeURIComponent(code)}/cancel`,
    null,
    { params: { email } },
  )
  return data
}
