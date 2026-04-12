import { type NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

// Python 파이프라인 루트 경로 (web/../ = Auto-Contects/)
const PIPELINE_ROOT = path.resolve(process.cwd(), '..')

interface GenerateRequest {
  categoryId: number
  topic: string
  type: 'shorts' | 'longform'
  language: 'ko' | 'en'
  tts: 'edge-tts' | 'elevenlabs' | 'typecast'
  imageStyle: number
  renderMode: 'auto' | 'studio' | 'capcut'
}

export async function POST(req: NextRequest) {
  let body: GenerateRequest
  try {
    body = await req.json() as GenerateRequest
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const { categoryId, topic, type, language, tts, imageStyle, renderMode } = body

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
  ]

  try {
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
