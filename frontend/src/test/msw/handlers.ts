import { http, HttpResponse } from 'msw'

const API = (path: string) => `*${path}`

export const handlers = [
  http.post(API('/api/v1/auth/login'), async ({ request }) => {
    const body = (await request.json()) as { email?: string; password?: string }
    if (body.email === 'admin@smarthotel.local' && body.password === 'admin') {
      return HttpResponse.json({
        accessToken: 'access-admin',
        role: 'ADMIN',
        email: 'admin@smarthotel.local',
        fullName: 'Admin User',
      })
    }
    if (body.email === 'recept@smarthotel.local' && body.password === 'recept') {
      return HttpResponse.json({
        accessToken: 'access-recept',
        role: 'RECEPTIONIST',
        email: 'recept@smarthotel.local',
        fullName: 'Reception User',
      })
    }
    return HttpResponse.json(
      {
        type: 'https://smarthotel/problems/unauthorized',
        title: 'Unauthorized',
        status: 401,
        detail: 'Invalid credentials',
      },
      { status: 401 },
    )
  }),

  http.post(API('/api/v1/auth/refresh'), () => {
    return HttpResponse.json({
      accessToken: 'access-refreshed',
      role: 'ADMIN',
      email: 'admin@smarthotel.local',
      fullName: 'Admin User',
    })
  }),

  http.post(API('/api/v1/auth/logout'), () => new HttpResponse(null, { status: 204 })),

  http.get(API('/api/v1/availability'), ({ request }) => {
    const url = new URL(request.url)
    const checkIn = url.searchParams.get('checkIn') ?? '2026-10-01'
    const checkOut = url.searchParams.get('checkOut') ?? '2026-10-03'
    return HttpResponse.json({
      checkIn,
      checkOut,
      guests: Number(url.searchParams.get('guests') ?? 2),
      roomTypes: [
        {
          code: 'STD',
          name: 'Standard',
          capacity: 2,
          roomsLeft: 3,
          nights: [
            { date: checkIn, bar: 280 },
            { date: checkIn, bar: 290 },
          ],
          ratePlans: [
            {
              code: 'FLEX',
              name: 'Flexible',
              refundable: true,
              breakfastIncluded: false,
              totalPrice: 570,
            },
          ],
        },
      ],
    })
  }),

  http.post(API('/api/v1/reservations'), async ({ request }) => {
    const body = (await request.json()) as {
      roomTypeCode?: string
      ratePlanCode?: string
      checkIn?: string
      checkOut?: string
      guest?: { email?: string; firstName?: string; lastName?: string }
    }
    return HttpResponse.json({
      id: 1,
      confirmationCode: 'ABC12345',
      status: 'CONFIRMED',
      roomType: body.roomTypeCode ?? 'STD',
      ratePlan: body.ratePlanCode ?? 'FLEX',
      checkIn: body.checkIn,
      checkOut: body.checkOut,
      guestEmail: body.guest?.email,
      guestName: `${body.guest?.firstName ?? ''} ${body.guest?.lastName ?? ''}`.trim(),
      totalPrice: 570,
      priceBreakdown: [],
    })
  }),

  http.get(API('/api/v1/reservations/lookup'), ({ request }) => {
    const url = new URL(request.url)
    return HttpResponse.json({
      id: 1,
      confirmationCode: url.searchParams.get('code')?.toUpperCase() ?? 'ABC12345',
      status: 'CONFIRMED',
      roomType: 'STD',
      ratePlan: 'FLEX',
      guestEmail: url.searchParams.get('email'),
      totalPrice: 570,
      priceBreakdown: [],
    })
  }),

  http.post(API('/api/v1/reservations/:code/cancel'), ({ params, request }) => {
    const url = new URL(request.url)
    return HttpResponse.json({
      id: 1,
      confirmationCode: String(params.code).toUpperCase(),
      status: 'CANCELLED',
      guestEmail: url.searchParams.get('email'),
      totalPrice: 570,
      priceBreakdown: [],
    })
  }),

  http.get(API('/api/v1/admin/reservations'), () =>
    HttpResponse.json({
      content: [
        {
          id: 10,
          confirmationCode: 'WALKIN01',
          status: 'CONFIRMED',
          guestName: 'Anna Nowak',
          guestEmail: 'anna@example.com',
          checkIn: '2026-10-01',
          checkOut: '2026-10-03',
          roomType: 'STD',
          roomNumber: '101',
          totalPrice: 570,
        },
      ],
      page: { number: 0, size: 50, totalElements: 1, totalPages: 1 },
    }),
  ),

  http.post(API('/api/v1/admin/reservations'), async ({ request }) => {
    const body = (await request.json()) as {
      roomTypeCode?: string
      ratePlanCode?: string
      checkIn?: string
      checkOut?: string
      guest?: { email?: string; firstName?: string; lastName?: string }
    }
    return HttpResponse.json({
      id: 99,
      confirmationCode: 'WALKIN99',
      status: 'CONFIRMED',
      roomType: body.roomTypeCode ?? 'STD',
      ratePlan: body.ratePlanCode ?? 'FLEX',
      checkIn: body.checkIn,
      checkOut: body.checkOut,
      guestEmail: body.guest?.email,
      guestName: `${body.guest?.firstName ?? ''} ${body.guest?.lastName ?? ''}`.trim(),
      totalPrice: 570,
      priceBreakdown: [],
    })
  }),

  http.get(API('/api/v1/admin/room-types'), () =>
    HttpResponse.json({
      content: [
        {
          id: 1,
          code: 'STD',
          name: 'Standard',
          capacity: 2,
          basePrice: 280,
          minPrice: 200,
          maxPrice: 500,
          active: true,
        },
      ],
      page: { number: 0, size: 100, totalElements: 1, totalPages: 1 },
    }),
  ),

  http.get(API('/api/v1/admin/rate-plans'), () =>
    HttpResponse.json([
      {
        id: 1,
        code: 'FLEX',
        name: 'Flexible',
        refundable: true,
        breakfastIncluded: false,
        priceModifier: 1,
        active: true,
        sortOrder: 1,
      },
      {
        id: 2,
        code: 'NRF',
        name: 'Non-refundable',
        refundable: false,
        breakfastIncluded: false,
        priceModifier: 0.9,
        active: true,
        sortOrder: 2,
      },
    ]),
  ),

  http.get(API('/api/v1/admin/rate-calendar'), ({ request }) => {
    const url = new URL(request.url)
    const from = url.searchParams.get('from') ?? '2026-10-01'
    return HttpResponse.json({
      roomTypeCode: url.searchParams.get('roomTypeCode') ?? 'STD',
      from,
      to: url.searchParams.get('to') ?? from,
      days: [
        {
          date: from,
          price: 320,
          source: 'ML_MODEL',
          demandIndicator: 70,
          fromCalendar: true,
        },
      ],
    })
  }),
]
