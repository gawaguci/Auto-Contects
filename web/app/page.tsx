import Link from 'next/link'
import { Container, Stack, Grid, Box } from './design-system/components/layout'
import { Heading, Text, Label } from './design-system/components/typography'
import { getJobs, getJobStatusLabel, type JobStatus } from './lib/jobs'
import { CATEGORIES } from './lib/categories'

const CATEGORY_CARD_COLOR: Record<number, string> = {
  1: 'var(--color-primary-100)',
  2: 'var(--color-warning-bg)',
  3: 'var(--color-primary-100)',
  4: 'var(--color-success-bg)',
  5: 'var(--color-warning-bg)',
  6: 'var(--color-info-bg)',
}

function StatusBadge({ status }: { status: JobStatus }) {
  const tone = status === 'completed'
    ? { bg: 'var(--state-success-bg)', fg: 'var(--state-success)' }
    : status === 'running'
      ? { bg: 'var(--state-info-bg)', fg: 'var(--state-info)' }
      : status === 'failed'
        ? { bg: 'var(--state-danger-bg)', fg: 'var(--state-danger)' }
        : { bg: 'var(--surface-overlay)', fg: 'var(--text-secondary)' }

  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: tone.bg, color: tone.fg }}
    >
      {getJobStatusLabel(status)}
    </span>
  )
}

export default async function HomePage() {
  const recentJobs = await getJobs(5)

  return (
    <div className="flex flex-col flex-1" style={{ background: 'var(--surface-default)' }}>
      <header
        className="border-b"
        style={{ background: 'var(--surface-raised)', borderColor: 'var(--border-default)' }}
      >
        <Container>
          <div className="flex items-center justify-between py-4">
            <Stack direction="row" gap="3" align="center">
              <Text size="xl" weight="semibold" color="brand">Auto Content</Text>
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{ background: 'var(--interactive-primary-bg)', color: 'var(--interactive-primary-text)' }}
              >
                v0.1
              </span>
            </Stack>
            <Text size="sm" color="secondary">유튜브 영상 자동 생성 파이프라인</Text>
          </div>
        </Container>
      </header>

      <main className="flex-1 py-8">
        <Container>
          <Stack gap="8">
            <div className="flex items-end justify-between">
              <Stack gap="1">
                <Heading level={1}>대시보드</Heading>
                <Text color="secondary">영상 카테고리를 선택하고 자동 생성을 시작하세요.</Text>
              </Stack>
              <Link
                href="/generate"
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
                style={{ background: 'var(--interactive-primary)', color: 'var(--text-inverse)' }}
              >
                ▶ 새 영상 생성
              </Link>
            </div>

            <Box>
              <Stack gap="4">
                <Label>카테고리</Label>
                <Grid cols={3} gap="4">
                  {CATEGORIES.map((cat) => (
                    <Link
                      key={cat.id}
                      href={`/generate?category=${cat.id}`}
                      className="block p-4 rounded-xl border transition-all hover:shadow-md"
                      style={{ background: CATEGORY_CARD_COLOR[cat.id] ?? 'var(--surface-raised)', borderColor: 'var(--border-default)' }}
                    >
                      <Stack gap="2">
                        <Text size="2xl">{cat.emoji}</Text>
                        <Text weight="semibold">{cat.name}</Text>
                        <Text size="xs" color="secondary">보이스: {cat.voice}</Text>
                      </Stack>
                    </Link>
                  ))}
                </Grid>
              </Stack>
            </Box>

            <Box>
              <Stack gap="4">
                <div className="flex items-center justify-between">
                  <Heading level={2} size="xl">최근 작업</Heading>
                  <Link
                    href="/jobs"
                    className="text-sm"
                    style={{ color: 'var(--text-brand)' }}
                  >
                    전체 보기 →
                  </Link>
                </div>
                <Box rounded="loose" border surface="raised" className="overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'var(--surface-overlay)' }}>
                        {['주제', '카테고리', '유형', '상태', '날짜'].map((h) => (
                          <th key={h} className="px-4 py-3 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {recentJobs.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                            아직 생성된 작업이 없습니다.
                          </td>
                        </tr>
                      ) : (
                        recentJobs.map((job, i) => (
                          <tr
                            key={job.id}
                            style={{ borderBottom: i < recentJobs.length - 1 ? '1px solid var(--border-subtle)' : undefined }}
                          >
                            <td className="px-4 py-3 font-medium" style={{ color: 'var(--text-primary)' }}>
                              {job.title ?? job.id}
                            </td>
                            <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{job.category ?? '—'}</td>
                            <td className="px-4 py-3" style={{ color: 'var(--text-secondary)' }}>{job.typeLabel ?? '—'}</td>
                            <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                            <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-tertiary)' }}>
                              {new Date(job.mtime).toLocaleDateString('ko-KR')}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </Box>
              </Stack>
            </Box>
          </Stack>
        </Container>
      </main>

      <footer className="border-t py-4" style={{ borderColor: 'var(--border-subtle)', background: 'var(--surface-overlay)' }}>
        <Container>
          <Text size="xs" color="tertiary" className="text-center">Auto Content — CLI 파이프라인 Web UI</Text>
        </Container>
      </footer>
    </div>
  )
}
