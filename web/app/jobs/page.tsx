import Link from 'next/link'
import { Container, Stack, Box } from '../design-system/components/layout'
import { Heading, Text } from '../design-system/components/typography'
import { getJobs, getJobStatusLabel, type JobStatus } from '../lib/jobs'

function JobStatusBadge({ status }: { status: JobStatus }) {
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

export default async function JobsPage() {
  const jobs = await getJobs()

  return (
    <div className="flex flex-col flex-1" style={{ background: 'var(--surface-default)' }}>
      <header className="border-b" style={{ background: 'var(--surface-raised)', borderColor: 'var(--border-default)' }}>
        <Container>
          <div className="flex items-center gap-3 py-4">
            <Link href="/" className="text-sm" style={{ color: 'var(--text-brand)' }}>← 대시보드</Link>
            <Text size="sm" color="tertiary">/</Text>
            <Text size="sm" color="secondary">작업 목록</Text>
          </div>
        </Container>
      </header>

      <main className="flex-1 py-8">
        <Container>
          <Stack gap="6">
            <div className="flex items-end justify-between">
              <Stack gap="1">
                <Heading level={1}>작업 목록</Heading>
                <Text color="secondary">
                  {jobs.length > 0
                    ? `${jobs.length}개의 작업이 있습니다.`
                    : 'output 폴더에 생성된 작업이 없습니다.'}
                </Text>
              </Stack>
              <Link
                href="/generate"
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
                style={{ background: 'var(--interactive-primary)', color: 'var(--text-inverse)' }}
              >
                ▶ 새 영상 생성
              </Link>
            </div>

            {jobs.length === 0 ? (
              <Box padding="8" surface="raised" rounded="loose" border className="text-center">
                <Stack gap="3" align="center">
                  <Text size="3xl">📂</Text>
                  <Text color="secondary">아직 생성된 영상이 없습니다.</Text>
                  <Link
                    href="/generate"
                    className="text-sm font-medium underline"
                    style={{ color: 'var(--text-brand)' }}
                  >
                    첫 번째 영상 만들기 →
                  </Link>
                </Stack>
              </Box>
            ) : (
              <Box surface="raised" rounded="loose" border className="overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'var(--surface-overlay)' }}>
                      {['Job ID', '상태', '제목', '출력 파일', '썸네일', '생성일'].map((h) => (
                        <th key={h} className="px-4 py-3 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job, i) => (
                      <tr
                        key={job.id}
                        style={{ borderBottom: i < jobs.length - 1 ? '1px solid var(--border-subtle)' : undefined }}
                      >
                        <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-primary)' }}>{job.id}</td>
                        <td className="px-4 py-3">
                          <Stack gap="1">
                            <JobStatusBadge status={job.status} />
                            {job.status === 'running' && job.step && (
                              <Text size="xs" color="secondary">{job.step}</Text>
                            )}
                          </Stack>
                        </td>
                        <td className="px-4 py-3" style={{ color: 'var(--text-primary)' }}>
                          {job.title ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          {job.hasOutputVideo ? (
                            <span style={{ color: 'var(--state-success)' }}>✓ {job.outputVideoFile ?? 'output.mp4'}</span>
                          ) : job.outputVideoFile ? (
                            <span style={{ color: 'var(--text-tertiary)' }}>예정: {job.outputVideoFile}</span>
                          ) : (
                            <span style={{ color: 'var(--text-disabled)' }}>—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {job.hasThumbnail
                            ? <span style={{ color: 'var(--state-success)' }}>✓ thumbnail.png</span>
                            : <span style={{ color: 'var(--text-disabled)' }}>—</span>}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {new Date(job.mtime).toLocaleDateString('ko-KR')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            )}
          </Stack>
        </Container>
      </main>
    </div>
  )
}
