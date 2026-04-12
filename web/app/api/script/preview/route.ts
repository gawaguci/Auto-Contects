import { type NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

const PIPELINE_ROOT = path.resolve(process.cwd(), '..')

interface ScriptPreviewRequest {
  categoryId: number
  topic: string
  type: 'shorts' | 'longform'
  language: 'ko' | 'en'
}

function runPython(args: string[]): Promise<{ code: number | null; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn('python', args, {
      cwd: PIPELINE_ROOT,
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
      },
      windowsHide: true,
    })

    let stdout = ''
    let stderr = ''

    proc.stdout.on('data', (chunk) => {
      stdout += String(chunk)
    })

    proc.stderr.on('data', (chunk) => {
      stderr += String(chunk)
    })

    proc.on('close', (code) => {
      resolve({ code, stdout, stderr })
    })
  })
}

function parseStdout(stdout: string): { script: unknown; prompt: unknown } {
  const lines = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length === 0) {
    throw new Error('빈 응답')
  }

  const jsonLine = lines[lines.length - 1]
  const parsed = JSON.parse(jsonLine) as { script?: unknown; prompt?: unknown }

  if (!parsed || typeof parsed !== 'object' || !parsed.script) {
    throw new Error('script 응답 형식이 올바르지 않습니다.')
  }

  return { script: parsed.script, prompt: parsed.prompt ?? null }
}

export async function POST(req: NextRequest) {
  let body: ScriptPreviewRequest
  try {
    body = await req.json() as ScriptPreviewRequest
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const { categoryId, topic, type, language } = body
  if (!Number.isInteger(categoryId) || categoryId < 1) {
    return NextResponse.json({ error: 'Invalid categoryId' }, { status: 400 })
  }
  if (!topic || !topic.trim()) {
    return NextResponse.json({ error: 'Invalid topic' }, { status: 400 })
  }

  const result = await runPython([
    '_script_preview_for_ui.py',
    `--category=${categoryId}`,
    `--topic=${topic}`,
    `--type=${type === 'longform' ? 'longform' : 'shorts'}`,
    `--language=${language === 'en' ? 'en' : 'ko'}`,
  ])

  if (result.code !== 0) {
    const reason = result.stderr.trim() || result.stdout.trim() || 'unknown error'
    return NextResponse.json(
      { error: `스크립트 프리뷰 생성 실패: ${reason}` },
      { status: 500 },
    )
  }

  try {
    const parsed = parseStdout(result.stdout)
    return NextResponse.json({ ok: true, script: parsed.script, prompt: parsed.prompt })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'JSON 파싱 실패'
    return NextResponse.json(
      { error: `스크립트 프리뷰 응답 파싱 실패: ${message}` },
      { status: 500 },
    )
  }
}