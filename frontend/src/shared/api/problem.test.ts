import { describe, expect, it } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { getProblemDetail, isProblemType, problemMessage } from '@/shared/api/problem'

describe('problem detail helpers', () => {
  it('extracts RFC 7807 fields from axios errors', () => {
    const error = new AxiosError(
      'Request failed',
      'ERR_BAD_REQUEST',
      { headers: new AxiosHeaders() },
      undefined,
      {
        status: 409,
        statusText: 'Conflict',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: {
          type: 'https://smarthotel/problems/room-no-longer-available',
          title: 'Room no longer available',
          status: 409,
          detail: 'No DLX room is free.',
          requestId: 'abc-123',
        },
      },
    )

    expect(getProblemDetail(error)?.detail).toBe('No DLX room is free.')
    expect(problemMessage(error, 'fallback')).toContain('No DLX room')
    expect(isProblemType(error, '/room-no-longer-available')).toBe(true)
  })

  it('falls back when the payload is not a problem', () => {
    expect(problemMessage(new Error('boom'), 'fallback')).toBe('fallback')
  })
})
