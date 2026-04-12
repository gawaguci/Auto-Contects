import { type NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

const PIPELINE_ROOT = path.resolve(process.cwd(), '..')

interface TopicItem {
  index: number
  title: string
  hook: string
  trend: string
  keywords: string[]
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

function parseTopicStdout(stdout: string): TopicItem[] {
  const lines = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  if (lines.length === 0) {
    throw new Error('빈 응답')
  }

  // 로깅이 섞인 경우 마지막 줄(JSON) 우선
  const jsonLine = lines[lines.length - 1]
  const parsed = JSON.parse(jsonLine) as TopicItem[]
  if (!Array.isArray(parsed)) {
    throw new Error('JSON 배열이 아닙니다.')
  }
  return parsed
}

export async function GET(req: NextRequest) {
  const raw = req.nextUrl.searchParams.get('categoryId')
  const categoryId = Number(raw)
  if (!Number.isInteger(categoryId) || categoryId < 1) {
    return NextResponse.json({ error: 'Invalid categoryId' }, { status: 400 })
  }

  const result = await runPython(['_topics_for_ui.py', `--category=${categoryId}`])
  if (result.code !== 0) {
    const reason = result.stderr.trim() || result.stdout.trim() || 'unknown error'
    return NextResponse.json(
      { error: `주제 생성 실패: ${reason}` },
      { status: 500 },
    )
  }

  try {
    const topics = parseTopicStdout(result.stdout)
    return NextResponse.json({ ok: true, topics })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'JSON 파싱 실패'
    return NextResponse.json(
      { error: `주제 응답 파싱 실패: ${message}` },
      { status: 500 },
    )
  }
}
