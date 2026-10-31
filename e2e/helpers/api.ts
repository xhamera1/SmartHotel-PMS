import { API_BASE, ADMIN_EMAIL, ADMIN_PASSWORD } from './env'

export type TokenBundle = {
  accessToken: string
  role: string
  email: string
  fullName: string
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.url}: ${body}`)
  }
  return (await res.json()) as T
}

export async function login(
  email = ADMIN_EMAIL,
  password = ADMIN_PASSWORD,
): Promise<TokenBundle> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return parseJson<TokenBundle>(res)
}

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
}

export async function createRoomType(
  token: string,
  code: string,
  opts?: { capacity?: number; basePrice?: number },
) {
  const base = opts?.basePrice ?? 300
  const res = await fetch(`${API_BASE}/api/v1/admin/room-types`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      code,
      name: `E2E ${code}`,
      description: 'Playwright seeded type',
      capacity: opts?.capacity ?? 2,
      basePrice: base,
      minPrice: Math.round(base * 0.7),
      maxPrice: Math.round(base * 1.8),
      amenities: ['WIFI'],
      active: true,
    }),
  })
  return parseJson<{ id: number; code: string }>(res)
}

export async function createRoom(token: string, roomTypeId: number, roomNumber: string) {
  const res = await fetch(`${API_BASE}/api/v1/admin/rooms`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      roomNumber,
      roomTypeId,
      floor: 1,
      status: 'AVAILABLE',
    }),
  })
  return parseJson<{ id: number; roomNumber: string }>(res)
}

export async function createPublicReservation(body: {
  roomTypeCode: string
  ratePlanCode?: string
  checkIn: string
  checkOut: string
  adults?: number
  guest: { email: string; firstName: string; lastName: string; phone?: string }
}) {
  const res = await fetch(`${API_BASE}/api/v1/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      roomTypeCode: body.roomTypeCode,
      ratePlanCode: body.ratePlanCode ?? 'FLEX',
      checkIn: body.checkIn,
      checkOut: body.checkOut,
      adults: body.adults ?? 2,
      guest: body.guest,
    }),
  })
  return parseJson<{
    id: number
    confirmationCode: string
    status: string
  }>(res)
}

export async function createAdminReservation(
  token: string,
  body: {
    roomTypeCode: string
    ratePlanCode?: string
    checkIn: string
    checkOut: string
    adults?: number
    guest: { email: string; firstName: string; lastName: string }
  },
) {
  const res = await fetch(`${API_BASE}/api/v1/admin/reservations`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      roomTypeCode: body.roomTypeCode,
      ratePlanCode: body.ratePlanCode ?? 'FLEX',
      checkIn: body.checkIn,
      checkOut: body.checkOut,
      adults: body.adults ?? 2,
      guest: body.guest,
    }),
  })
  return parseJson<{ id: number; confirmationCode: string; status: string }>(res)
}

export async function putManualRate(
  token: string,
  roomTypeCode: string,
  date: string,
  price: number,
) {
  const res = await fetch(
    `${API_BASE}/api/v1/admin/rate-calendar/${encodeURIComponent(roomTypeCode)}/${date}`,
    {
      method: 'PUT',
      headers: authHeaders(token),
      body: JSON.stringify({ price }),
    },
  )
  return parseJson<{ date: string; price: number; source: string }>(res)
}

export async function refreshPrices(token: string) {
  const res = await fetch(`${API_BASE}/api/v1/admin/pricing/refresh`, {
    method: 'POST',
    headers: authHeaders(token),
  })
  return parseJson<{ status?: string; message?: string }>(res)
}

export async function syncEvents(internalKey = 'dev-internal-api-key') {
  const res = await fetch('http://localhost:8081/internal/events/sync', {
    method: 'POST',
    headers: { 'X-Internal-Api-Key': internalKey, Accept: 'application/json' },
  })
  if (res.status !== 202 && !res.ok) {
    const body = await res.text()
    throw new Error(`events sync ${res.status}: ${body}`)
  }
}

export function uniqueCode(prefix: string, workerIndex: number): string {
  // Room type codes ≤ 30
  const suffix = Math.random().toString(36).slice(2, 6).toUpperCase()
  return `${prefix}${workerIndex}${suffix}`.slice(0, 8)
}

/** Globally unique room numbers (API constraint ≤ 10 chars). */
export function uniqueRoomNumber(workerIndex: number): string {
  const suffix = Math.random().toString(36).slice(2, 8).toUpperCase()
  return `R${workerIndex}${suffix}`.slice(0, 10)
}

export function uniqueEmail(tag: string, workerIndex: number): string {
  return `e2e-${tag}-w${workerIndex}-${Date.now()}@example.com`
}
