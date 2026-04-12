import { readdir, readFile, stat } from 'fs/promises'
import path from 'path'

const OUTPUT_DIR = path.resolve(process.cwd(), '..', 'output')
const JOB_ID_PATTERN = /^\d{8}_\d+$/
const STATUS_FILE_NAME = 'job_status.json'

export type JobStatus = 'running' | 'completed' | 'failed' | 'stopped'

interface StatusFilePayload {
  status?: string
  pid?: number
  step?: string
  output_video?: string
  error?: string
  updated_at?: string
  progress?: {
    current?: number
    total?: number
  }
}

export interface Job {
  id: string
  pid: number | null
  mtime: number
  status: JobStatus
  hasThumbnail: boolean
  hasOutputVideo: boolean
  outputVideoFile: string | null
  step: string | null
  title: string | null
  category: string | null
  typeLabel: string | null
  error: string | null
  updatedAt: string | null
  progressCurrent: number | null
  progressTotal: number | null
}

function normalizeStatus(value: string | undefined): JobStatus | null {
  if (value === 'running' || value === 'completed' || value === 'failed' || value === 'stopped') {
    return value
  }
  return null
}

function isProcessAlive(pid: number | undefined): boolean {
  if (!pid || pid <= 0) return false
  try {
    process.kill(pid, 0)
    return true
  } catch (error: unknown) {
    if (
      typeof error === 'object' &&
      error !== null &&
      'code' in error &&
      (error as { code?: string }).code === 'EPERM'
    ) {
      return true
    }
    return false
  }
}

function pickOutputVideo(files: string[]): string | null {
  const mp4s = files.filter((f) => f.toLowerCase().endsWith('.mp4'))
  if (mp4s.length === 0) return null

  const nonTemp = mp4s.filter((f) => f.toLowerCase() !== 'video_only.mp4')
  const candidates = nonTemp.length > 0 ? nonTemp : mp4s
  candidates.sort((a, b) => a.localeCompare(b))
  return candidates[0]
}

async function readJsonFile(filePath: string): Promise<Record<string, unknown> | null> {
  try {
    const raw = await readFile(filePath, 'utf-8')
    return JSON.parse(raw) as Record<string, unknown>
  } catch {
    return null
  }
}

export function resolveJobStatus(params: {
  hasVideo: boolean
  statusFileState: JobStatus | null
  pidAlive: boolean
}): JobStatus {
  const { hasVideo, statusFileState, pidAlive } = params

  if (hasVideo || statusFileState === 'completed') return 'completed'
  if (statusFileState === 'failed') return 'failed'
  if (statusFileState === 'stopped') return 'stopped'
  if (statusFileState === 'running') return pidAlive ? 'running' : 'stopped'
  return 'stopped'
}

export function getJobStatusLabel(status: JobStatus): string {
  if (status === 'completed') return '완료'
  if (status === 'running') return '진행중'
  if (status === 'failed') return '실패'
  return '중단됨'
}

export async function getJobs(limit?: number): Promise<Job[]> {
  try {
    const entries = await readdir(OUTPUT_DIR, { withFileTypes: true })
    const jobs: Job[] = []

    for (const entry of entries) {
      if (!entry.isDirectory()) continue
      if (!JOB_ID_PATTERN.test(entry.name)) continue

      const jobPath = path.join(OUTPUT_DIR, entry.name)
      const s = await stat(jobPath)
      const files = await readdir(jobPath).catch(() => [] as string[])

      const outputVideoFile = pickOutputVideo(files)
      const hasVideo = Boolean(outputVideoFile)
      const hasThumbnail = files.includes('thumbnail.png')

      const statusPayload = await readJsonFile(path.join(jobPath, STATUS_FILE_NAME))
      const statusFile = (statusPayload ?? null) as StatusFilePayload | null
      const statusFileState = normalizeStatus(statusFile?.status)
      const pidAlive = isProcessAlive(statusFile?.pid)
      const status = resolveJobStatus({ hasVideo, statusFileState, pidAlive })

      const metadata = await readJsonFile(path.join(jobPath, 'metadata.json'))
      const remotionInput = await readJsonFile(path.join(jobPath, 'remotion_input.json'))

      const metaTitle = typeof metadata?.title === 'string' ? metadata.title : null
      const remotionTitle = typeof remotionInput?.title === 'string' ? remotionInput.title : null
      const category = typeof remotionInput?.category === 'string' ? remotionInput.category : null
      const version = typeof remotionInput?.version === 'string' ? remotionInput.version : null
      const typeLabel = version === 'shorts' ? '숏츠' : version === 'longform' ? '롱폼' : null

      jobs.push({
        id: entry.name,
        pid: typeof statusFile?.pid === 'number' ? statusFile.pid : null,
        mtime: s.mtimeMs,
        status,
        hasThumbnail,
        hasOutputVideo: hasVideo,
        outputVideoFile: outputVideoFile ?? statusFile?.output_video ?? null,
        step: typeof statusFile?.step === 'string' ? statusFile.step : null,
        title: metaTitle ?? remotionTitle,
        category,
        typeLabel,
        error: typeof statusFile?.error === 'string' ? statusFile.error : null,
        updatedAt: typeof statusFile?.updated_at === 'string' ? statusFile.updated_at : null,
        progressCurrent: typeof statusFile?.progress?.current === 'number' ? statusFile.progress.current : null,
        progressTotal: typeof statusFile?.progress?.total === 'number' ? statusFile.progress.total : null,
      })
    }

    const sorted = jobs.sort((a, b) => b.mtime - a.mtime)
    return typeof limit === 'number' ? sorted.slice(0, limit) : sorted
  } catch {
    return []
  }
}

