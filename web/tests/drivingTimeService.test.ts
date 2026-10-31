import type { Mock } from 'vitest'
import type { GeographicPoint } from '../app/types/Location'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DrivingTimeService } from '../app/services/drivingTimeService'

const RENNES: GeographicPoint = { latitude: 48.117, longitude: -1.678 }
const BAIN_DE_BRETAGNE: GeographicPoint = { latitude: 47.841, longitude: -1.674 }
const REDON: GeographicPoint = { latitude: 47.651, longitude: -2.084 }

/**
 * Stand in for the router with a fixed answer.
 *
 * @param answer - The JSON the router gives.
 * @returns The fake fetch, to check the request it got.
 */
function answerWith(answer: unknown): Mock<() => Promise<Response>> {
  const fakeFetch: Mock<() => Promise<Response>> = vi.fn((): Promise<Response> =>
    Promise.resolve(Response.json(answer)),
  )
  vi.stubGlobal('fetch', fakeFetch)
  return fakeFetch
}

afterEach((): void => {
  vi.unstubAllGlobals()
})

describe('DrivingTimeService.fetchMinutes', (): void => {
  it('reads every drive from a single answer of the router', async (): Promise<void> => {
    const fakeFetch: Mock<() => Promise<Response>> = answerWith({ code: 'Ok', durations: [[0, 2226.3, 3400]] })

    await expect(DrivingTimeService.fetchMinutes(RENNES, [BAIN_DE_BRETAGNE, REDON])).resolves.toEqual([37, 57])
    expect(fakeFetch).toHaveBeenCalledWith(
      'https://router.project-osrm.org/table/v1/driving/-1.678,48.117;-1.674,47.841;-2.084,47.651?sources=0&annotations=duration',
    )
  })

  it('gives no time for a drive without a route, or when the router is out of reach', async (): Promise<void> => {
    answerWith({ code: 'Ok', durations: [[0, null]] })
    await expect(DrivingTimeService.fetchMinutes(RENNES, [REDON])).resolves.toEqual([null])

    vi.stubGlobal(
      'fetch',
      vi.fn((): Promise<Response> => Promise.reject(new TypeError('Failed to fetch'))),
    )
    await expect(DrivingTimeService.fetchMinutes(RENNES, [REDON])).resolves.toEqual([null])
  })
})
