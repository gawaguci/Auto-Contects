import { type NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { mkdir, writeFile } from 'fs/promises'
import path from 'path'

// Python 파이프라인 루트 경로 (web/../ = Auto-Contects/)
const PIPELINE_ROOT = path.resolve(process.cwd(), '..')

type PlaybackSpeed = 30 | 20 | 15 | 10 | 0 | -10 | -20

interface ScriptSceneOverride {
  index: number
  duration?: number
  narration: string
  subtitle: string
  imagePrompt?: string
  bgColor?: string
  videoQuery?: string
}

interface ScriptOverride {
  title: string
  cta?: string
  scenes: ScriptSceneOverride[]
}

interface GenerateRequest {
  categoryId: number
  topic: string
  type: 'shorts' | 'longform'
  language: 'ko' | 'en'
  tts: 'edge-tts' | 'elevenlabs' | 'typecast'
  imageStyle: number
  renderMode: 'auto' | 'studio' | 'capcut'
  playbackSpeed?: PlaybackSpeed
  scriptOverride?: ScriptOverride | null
}

function normalizePlaybackSpeed(value: unknown): PlaybackSpeed {
  return value === 30 || value === 20 || value === 15 || value === 10 || value === -10 || value === -20 ? value : 0
}

async function writeScriptOverrideFile(payload: ScriptOverride): Promise<string> {
  const tmpDir = path.join(PIPELINE_ROOT, '.tmp', 'ui-script-overrides')
  await mkdir(tmpDir, { recursive: true })
  const fileName = `script_${Date.now()}_${Math.random().toString(36).slice(2, 10)}.json`
  const filePath = path.join(tmpDir, fileName)
  await writeFile(filePath, JSON.stringify(payload, null, 2), 'utf-8')
  return filePath
}

export async function POST(req: NextRequest) {
  let body: GenerateRequest
  try {
    body = await req.json() as GenerateRequest
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const { categoryId, topic, type, language, tts, imageStyle, renderMode } = body
  const playbackSpeed = renderMode === 'capcut' ? 0 : normalizePlaybackSpeed(body.playbackSpeed)

  // _run_pipeline.py --auto 인자 조합
  const args = [
    '_run_pipeline.py',
    '--auto',
    `--category=${categoryId}`,
    `--topic=${topic}`,
    `--type=${type === 'shorts' ? 'shorts' : 'longform'}`,
    `--language=${language}`,
    `--tts=${tts}`,
    `--image-style=${imageStyle}`,
    `--render=${renderMode}`,
    `--playback-speed=${playbackSpeed}`,
  ]

  try {
    if (body.scriptOverride && Array.isArray(body.scriptOverride.scenes) && body.scriptOverride.scenes.length > 0) {
      const scriptPath = await writeScriptOverrideFile(body.scriptOverride)
      args.push(`--script-json=${scriptPath}`)
    }

    const proc = spawn('python', args, {
      cwd: PIPELINE_ROOT,
      detached: true,
      stdio: 'ignore',
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
      },
    })
    proc.unref()

    return NextResponse.json(
      { ok: true, status: 'started', pid: proc.pid ?? null },
      { status: 202 },
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : '알 수 없는 오류'
    return NextResponse.json(
      { ok: false, error: `프로세스 실행 실패: ${message}` },
      { status: 500 },
    )
  }
}