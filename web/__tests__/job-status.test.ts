// @vitest-environment node

import { describe, expect, it } from 'vitest'

import { resolveJobStatus } from '../app/lib/jobs'

describe('resolveJobStatus', () => {
  it('returns completed when output video exists', () => {
    const status = resolveJobStatus({
      hasVideo: true,
      statusFileState: null,
      pidAlive: false,
    })
    expect(status).toBe('completed')
  })

  it('returns running when status is running and process is alive', () => {
    const status = resolveJobStatus({
      hasVideo: false,
      statusFileState: 'running',
      pidAlive: true,
    })
    expect(status).toBe('running')
  })

  it('returns stopped when status is running but process is not alive', () => {
    const status = resolveJobStatus({
      hasVideo: false,
      statusFileState: 'running',
      pidAlive: false,
    })
    expect(status).toBe('stopped')
  })

  it('returns failed when status file says failed', () => {
    const status = resolveJobStatus({
      hasVideo: false,
      statusFileState: 'failed',
      pidAlive: false,
    })
    expect(status).toBe('failed')
  })

  it('returns stopped when no status/video exists', () => {
    const status = resolveJobStatus({
      hasVideo: false,
      statusFileState: null,
      pidAlive: false,
    })
    expect(status).toBe('stopped')
  })
})
