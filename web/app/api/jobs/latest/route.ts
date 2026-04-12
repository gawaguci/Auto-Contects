import { NextResponse } from 'next/server'
import { getJobs } from '../../../lib/jobs'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  const jobs = await getJobs(1)
  return NextResponse.json({ job: jobs[0] ?? null }, { status: 200 })
}

