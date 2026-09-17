import { apiClient } from '@/shared/api/client'
import type { components } from '@/shared/api/schema'

export type DashboardKpis = components['schemas']['DashboardKpisResponse']
export type DashboardTimeseries = components['schemas']['DashboardTimeseriesResponse']
export type RoomType = components['schemas']['RoomTypeResponse']
export type Room = components['schemas']['RoomResponse']
export type Guest = components['schemas']['GuestResponse']
export type AdminReservation = components['schemas']['AdminReservationSummary']
export type ReservationDetail = components['schemas']['ReservationResponse']
export type RateCalendar = components['schemas']['RateCalendarResponse']
export type RateCalendarDay = components['schemas']['RateCalendarDayResponse']
export type PricingEvent = components['schemas']['PricingEventResponse']
export type DemandPoint = components['schemas']['DemandIndicatorPoint']
export type PricingRefresh = components['schemas']['PricingRefreshResponse']
export type CreateRoomTypeRequest = components['schemas']['CreateRoomTypeRequest']
export type UpdateRoomTypeRequest = components['schemas']['UpdateRoomTypeRequest']
export type CreateRoomRequest = components['schemas']['CreateRoomRequest']
export type UpdateRoomRequest = components['schemas']['UpdateRoomRequest']
export type CreateReservationRequest = components['schemas']['CreateReservationRequest']
export type RatePlan = components['schemas']['RatePlanResponse']

export type PageMeta = components['schemas']['PageMeta']

export const adminKeys = {
  kpis: ['admin', 'dashboard', 'kpis'] as const,
  timeseries: (days: number) => ['admin', 'dashboard', 'timeseries', days] as const,
  roomTypes: (params: Record<string, unknown>) => ['admin', 'room-types', params] as const,
  rooms: (params: Record<string, unknown>) => ['admin', 'rooms', params] as const,
  guests: (params: Record<string, unknown>) => ['admin', 'guests', params] as const,
  reservations: (params: Record<string, unknown>) => ['admin', 'reservations', params] as const,
  reservation: (id: number) => ['admin', 'reservations', 'detail', id] as const,
  ratePlans: ['admin', 'rate-plans'] as const,
  rateCalendar: (roomTypeCode: string, from: string, to: string) =>
    ['admin', 'rate-calendar', roomTypeCode, from, to] as const,
  events: (from: string, to: string) => ['admin', 'pricing', 'events', from, to] as const,
  demand: (from: string, to: string) => ['admin', 'pricing', 'demand', from, to] as const,
}

export async function fetchKpis() {
  const { data } = await apiClient.get<DashboardKpis>('/api/v1/admin/dashboard/kpis')
  return data
}

export async function fetchTimeseries(days = 30) {
  const { data } = await apiClient.get<DashboardTimeseries>('/api/v1/admin/dashboard/timeseries', {
    params: { days },
  })
  return data
}

export async function fetchRoomTypes(params: {
  page?: number
  size?: number
  active?: boolean
  query?: string
}) {
  const { data } = await apiClient.get<{ content?: RoomType[]; page?: PageMeta }>(
    '/api/v1/admin/room-types',
    { params },
  )
  return data
}

export async function createRoomType(body: CreateRoomTypeRequest) {
  const { data } = await apiClient.post<RoomType>('/api/v1/admin/room-types', body)
  return data
}

export async function updateRoomType(id: number, body: UpdateRoomTypeRequest) {
  const { data } = await apiClient.put<RoomType>(`/api/v1/admin/room-types/${id}`, body)
  return data
}

export async function deleteRoomType(id: number) {
  await apiClient.delete(`/api/v1/admin/room-types/${id}`)
}

export async function fetchRooms(params: { page?: number; size?: number; roomTypeId?: number }) {
  const { data } = await apiClient.get<{ content?: Room[]; page?: PageMeta }>(
    '/api/v1/admin/rooms',
    {
      params,
    },
  )
  return data
}

export async function createRoom(body: CreateRoomRequest) {
  const { data } = await apiClient.post<Room>('/api/v1/admin/rooms', body)
  return data
}

export async function updateRoom(id: number, body: UpdateRoomRequest) {
  const { data } = await apiClient.put<Room>(`/api/v1/admin/rooms/${id}`, body)
  return data
}

export async function fetchGuests(params: { page?: number; size?: number; query?: string }) {
  const { data } = await apiClient.get<{ content?: Guest[]; page?: PageMeta }>(
    '/api/v1/admin/guests',
    {
      params,
    },
  )
  return data
}

export async function fetchReservations(params: {
  page?: number
  size?: number
  status?: string
  from?: string
  to?: string
  query?: string
}) {
  const { data } = await apiClient.get<{ content?: AdminReservation[]; page?: PageMeta }>(
    '/api/v1/admin/reservations',
    { params },
  )
  return data
}

export async function fetchReservation(id: number) {
  const { data } = await apiClient.get<ReservationDetail>(`/api/v1/admin/reservations/${id}`)
  return data
}

export async function createAdminReservation(body: CreateReservationRequest) {
  const { data } = await apiClient.post<ReservationDetail>('/api/v1/admin/reservations', body)
  return data
}

export async function reservationAction(
  id: number,
  action: 'check-in' | 'check-out' | 'cancel' | 'no-show',
) {
  const { data } = await apiClient.post<ReservationDetail>(
    `/api/v1/admin/reservations/${id}/${action}`,
  )
  return data
}

export async function fetchRatePlans() {
  const { data } = await apiClient.get<RatePlan[]>('/api/v1/admin/rate-plans')
  return data
}

export async function fetchRateCalendar(roomTypeCode: string, from: string, to: string) {
  const { data } = await apiClient.get<RateCalendar>('/api/v1/admin/rate-calendar', {
    params: { roomTypeCode, from, to },
  })
  return data
}

export async function putManualRate(roomTypeCode: string, date: string, price: number) {
  const { data } = await apiClient.put<RateCalendarDay>(
    `/api/v1/admin/rate-calendar/${encodeURIComponent(roomTypeCode)}/${date}`,
    { price },
  )
  return data
}

export async function deleteManualRate(roomTypeCode: string, date: string) {
  await apiClient.delete(`/api/v1/admin/rate-calendar/${encodeURIComponent(roomTypeCode)}/${date}`)
}

export async function refreshPrices() {
  const { data } = await apiClient.post<PricingRefresh>('/api/v1/admin/pricing/refresh')
  return data
}

export async function fetchEvents(from: string, to: string) {
  const { data } = await apiClient.get<PricingEvent[]>('/api/v1/admin/pricing/events', {
    params: { from, to },
  })
  return data
}

export async function fetchDemandIndicators(from: string, to: string) {
  const { data } = await apiClient.get<DemandPoint[]>('/api/v1/admin/pricing/demand-indicators', {
    params: { from, to },
  })
  return data
}
