'use client'

import { useState } from 'react'
import { Container, Stack, Box, Grid } from '../design-system/components/layout'
import { Heading, Text, Label } from '../design-system/components/typography'
import Link from 'next/link'
import { CATEGORIES, type CategoryOption } from '../lib/categories'

// ── Types ──────────────────────────────────────────────────────────────────

type Step = 'category' | 'topic' | 'options' | 'confirm'

type Category = CategoryOption

interface TopicOption {
  index: number
  title: string
  hook: string
  trend: string
  keywords: string[]
}

interface GenerateOptions {
  type: 'shorts' | 'longform'
  language: 'ko' | 'en'
  tts: 'edge-tts' | 'elevenlabs' | 'typecast'
  imageStyle: number
  renderMode: 'auto' | 'studio' | 'capcut'
}

// ── Static Data ─────────────────────────────────────────────────────────────

const IMAGE_STYLES = [
  { id: 0, name: '화풍 없음 (기본)' },
  { id: 1, name: '시네마틱 실사' },
  { id: 2, name: '수채화' },
  { id: 3, name: '카툰/만화' },
  { id: 4, name: '애니메이션' },
  { id: 5, name: '유화' },
  { id: 6, name: '연필 스케치' },
  { id: 7, name: '흰 얼굴 캐릭터' },
]

// ── Step indicator ───────────────────────────────────────────────────────────

const STEPS: { key: Step; label: string }[] = [
  { key: 'category', label: '카테고리' },
  { key: 'topic',    label: '주제' },
  { key: 'options',  label: '옵션' },
  { key: 'confirm',  label: '확인' },
]

function StepBar({ current }: { current: Step }) {
  const idx = STEPS.findIndex(s => s.key === current)
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => (
        <div key={step.key} className="flex items-center">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold"
              style={{
                background: i <= idx ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
                color: i <= idx ? 'var(--text-inverse)' : 'var(--text-tertiary)',
              }}
            >
              {i < idx ? '✓' : i + 1}
            </div>
            <Text size="sm" color={i <= idx ? 'primary' : 'tertiary'} weight={i === idx ? 'semibold' : 'normal'}>
              {step.label}
            </Text>
          </div>
          {i < STEPS.length - 1 && (
            <div
              className="w-8 h-px mx-2"
              style={{ background: i < idx ? 'var(--interactive-primary)' : 'var(--border-default)' }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

// ── Step 1: Category ─────────────────────────────────────────────────────────

function CategoryStep({
  onSelect,
}: {
  onSelect: (cat: Category) => void
}) {
  return (
    <Stack gap="4">
      <Stack gap="1">
        <Heading level={2}>카테고리 선택</Heading>
        <Text color="secondary">생성할 영상의 카테고리를 선택하세요.</Text>
      </Stack>
      <Grid cols={3} gap="3">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => onSelect(cat)}
            className="text-left p-4 rounded-xl border transition-all hover:shadow-md"
            style={{
              background: 'var(--surface-raised)',
              borderColor: 'var(--border-default)',
            }}
          >
            <Stack gap="2">
              <Text size="2xl">{cat.emoji}</Text>
              <Text weight="semibold">{cat.name}</Text>
              <Text size="xs" color="secondary">보이스: {cat.voice}</Text>
            </Stack>
          </button>
        ))}
      </Grid>
    </Stack>
  )
}

// ── Step 2: Topic ────────────────────────────────────────────────────────────

function TopicStep({
  category,
  topics,
  loading,
  error,
  onRetry,
  onSelect,
  onBack,
}: {
  category: Category
  topics: TopicOption[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onSelect: (topic: string) => void
  onBack: () => void
}) {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <Stack gap="4">
      <Stack gap="1">
        <Heading level={2}>주제 선택</Heading>
        <Text color="secondary">
          <span style={{ color: 'var(--interactive-primary-text)' }}>{category.emoji} {category.name}</span>
          &nbsp;카테고리의 주제를 선택하세요.
        </Text>
      </Stack>

      {loading && (
        <Box padding="4" surface="raised" rounded="loose" border>
          <Text color="secondary">주제를 생성하는 중입니다...</Text>
        </Box>
      )}

      {error && !loading && (
        <Box padding="4" surface="raised" rounded="loose" border>
          <Stack gap="3">
            <Text size="sm" style={{ color: 'var(--state-danger)' }}>{error}</Text>
            <button
              onClick={onRetry}
              className="px-3 py-2 rounded-lg text-sm font-medium border self-start"
              style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}
            >
              다시 불러오기
            </button>
          </Stack>
        </Box>
      )}

      {!loading && !error && (
        <Stack gap="2">
          {topics.map((item, i) => (
            <button
              key={item.index}
              onClick={() => setSelected(item.title)}
              className="text-left p-4 rounded-lg border transition-all"
              style={{
                background: selected === item.title ? 'var(--interactive-primary-bg)' : 'var(--surface-raised)',
                borderColor: selected === item.title ? 'var(--border-focus)' : 'var(--border-default)',
              }}
            >
              <Stack gap="1">
                <Stack direction="row" gap="3" align="center">
                  <Text
                    size="sm"
                    className="w-6 h-6 rounded-full flex items-center justify-center font-semibold shrink-0"
                    style={{
                      background: selected === item.title ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
                      color: selected === item.title ? 'var(--text-inverse)' : 'var(--text-secondary)',
                    }}
                  >
                    {i + 1}
                  </Text>
                  <Text weight={selected === item.title ? 'medium' : 'normal'}>{item.title}</Text>
                </Stack>
                {item.trend && (
                  <Text size="xs" color="secondary" className="pl-9">{item.trend}</Text>
                )}
              </Stack>
            </button>
          ))}
        </Stack>
      )}

      <Stack direction="row" gap="3">
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-lg text-sm font-medium border"
          style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}
        >
          ← 뒤로
        </button>
        <button
          onClick={() => selected && onSelect(selected)}
          disabled={!selected || loading || !!error}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{
            background: selected && !loading && !error ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
            color: selected && !loading && !error ? 'var(--text-inverse)' : 'var(--text-disabled)',
            cursor: selected && !loading && !error ? 'pointer' : 'not-allowed',
          }}
        >
          다음 →
        </button>
      </Stack>
    </Stack>
  )
}

// ── Step 3: Options ───────────────────────────────────────────────────────────

function OptionButton({
  label,
  selected,
  onClick,
}: {
  label: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 rounded-lg text-sm font-medium border transition-all"
      style={{
        background: selected ? 'var(--interactive-primary-bg)' : 'var(--surface-raised)',
        borderColor: selected ? 'var(--border-focus)' : 'var(--border-default)',
        color: selected ? 'var(--interactive-primary-text)' : 'var(--text-primary)',
      }}
    >
      {label}
    </button>
  )
}

function OptionsStep({
  options,
  onChange,
  onNext,
  onBack,
}: {
  options: GenerateOptions
  onChange: (o: Partial<GenerateOptions>) => void
  onNext: () => void
  onBack: () => void
}) {
  return (
    <Stack gap="5">
      <Stack gap="1">
        <Heading level={2}>옵션 설정</Heading>
        <Text color="secondary">영상 생성 세부 옵션을 설정하세요.</Text>
      </Stack>

      {/* Type */}
      <Box>
        <Stack gap="2">
          <Label>영상 유형</Label>
          <Stack direction="row" gap="2">
            <OptionButton label="🎬 쇼츠 (90초)" selected={options.type === 'shorts'} onClick={() => onChange({ type: 'shorts' })} />
            <OptionButton label="📽 롱폼 (10분)" selected={options.type === 'longform'} onClick={() => onChange({ type: 'longform' })} />
          </Stack>
        </Stack>
      </Box>

      {/* Language */}
      <Box>
        <Stack gap="2">
          <Label>언어</Label>
          <Stack direction="row" gap="2">
            <OptionButton label="🇰🇷 한국어" selected={options.language === 'ko'} onClick={() => onChange({ language: 'ko' })} />
            <OptionButton label="🇺🇸 영어" selected={options.language === 'en'} onClick={() => onChange({ language: 'en' })} />
          </Stack>
        </Stack>
      </Box>

      {/* TTS */}
      <Box>
        <Stack gap="2">
          <Label>TTS 공급자</Label>
          <Stack direction="row" gap="2">
            <OptionButton label="Edge-TTS (무료)" selected={options.tts === 'edge-tts'} onClick={() => onChange({ tts: 'edge-tts' })} />
            <OptionButton label="ElevenLabs (유료)" selected={options.tts === 'elevenlabs'} onClick={() => onChange({ tts: 'elevenlabs' })} />
            <OptionButton label="Typecast (유료)" selected={options.tts === 'typecast'} onClick={() => onChange({ tts: 'typecast' })} />
          </Stack>
        </Stack>
      </Box>

      {/* Image Style */}
      <Box>
        <Stack gap="2">
          <Label>이미지 스타일</Label>
          <Grid cols={4} gap="2">
            {IMAGE_STYLES.map((style) => (
              <OptionButton
                key={style.id}
                label={style.name}
                selected={options.imageStyle === style.id}
                onClick={() => onChange({ imageStyle: style.id })}
              />
            ))}
          </Grid>
        </Stack>
      </Box>

      {/* Render Mode */}
      <Box>
        <Stack gap="2">
          <Label>렌더링 방식</Label>
          <Stack direction="row" gap="2">
            <OptionButton label="⚡ 자동 렌더링" selected={options.renderMode === 'auto'} onClick={() => onChange({ renderMode: 'auto' })} />
            <OptionButton label="🎥 Remotion Studio" selected={options.renderMode === 'studio'} onClick={() => onChange({ renderMode: 'studio' })} />
            <OptionButton label="✂️ 캡컷 프로젝트" selected={options.renderMode === 'capcut'} onClick={() => onChange({ renderMode: 'capcut' })} />
          </Stack>
        </Stack>
      </Box>

      <Stack direction="row" gap="3">
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-lg text-sm font-medium border"
          style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}
        >
          ← 뒤로
        </button>
        <button
          onClick={onNext}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ background: 'var(--interactive-primary)', color: 'var(--text-inverse)' }}
        >
          다음 →
        </button>
      </Stack>
    </Stack>
  )
}

// ── Step 4: Confirm ───────────────────────────────────────────────────────────

function ConfirmStep({
  category,
  topic,
  options,
  onStart,
  onBack,
}: {
  category: Category
  topic: string
  options: GenerateOptions
  onStart: () => void
  onBack: () => void
}) {
  const typeLabel = options.type === 'shorts' ? '쇼츠 (90초)' : '롱폼 (10분)'
  const langLabel = options.language === 'ko' ? '한국어' : '영어'
  const ttsLabel = options.tts === 'edge-tts' ? 'Edge-TTS (무료)' : options.tts === 'elevenlabs' ? 'ElevenLabs' : 'Typecast'
  const styleLabel = IMAGE_STYLES.find(s => s.id === options.imageStyle)?.name ?? '화풍 없음'
  const renderLabel = options.renderMode === 'auto' ? '자동 렌더링' : options.renderMode === 'studio' ? 'Remotion Studio' : '캡컷 프로젝트'

  const rows = [
    { label: '카테고리', value: `${category.emoji} ${category.name}` },
    { label: '주제', value: topic },
    { label: '유형', value: typeLabel },
    { label: '언어', value: langLabel },
    { label: 'TTS', value: ttsLabel },
    { label: '이미지 스타일', value: styleLabel },
    { label: '렌더링', value: renderLabel },
  ]

  return (
    <Stack gap="5">
      <Stack gap="1">
        <Heading level={2}>생성 확인</Heading>
        <Text color="secondary">설정을 확인하고 영상 생성을 시작하세요.</Text>
      </Stack>

      <Box padding="4" surface="raised" rounded="loose" border>
        <Stack gap="0">
          {rows.map((row, i) => (
            <div
              key={row.label}
              className="flex items-start gap-4 py-3"
              style={{
                borderBottom: i < rows.length - 1 ? '1px solid var(--border-subtle)' : undefined,
              }}
            >
              <Text size="sm" color="secondary" className="w-24 shrink-0">{row.label}</Text>
              <Text size="sm" weight={row.label === '주제' ? 'medium' : 'normal'}>{row.value}</Text>
            </div>
          ))}
        </Stack>
      </Box>

      <Stack direction="row" gap="3">
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-lg text-sm font-medium border"
          style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}
        >
          ← 뒤로
        </button>
        <button
          onClick={onStart}
          className="flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold"
          style={{ background: 'var(--interactive-primary)', color: 'var(--text-inverse)' }}
        >
          ▶ 영상 생성 시작
        </button>
      </Stack>
    </Stack>
  )
}

// ── Running State ─────────────────────────────────────────────────────────────

function RunningState({ category, topic }: { category: Category; topic: string }) {
  return (
    <Stack gap="6" align="center" className="py-12">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center text-3xl animate-pulse"
        style={{ background: 'var(--interactive-primary-bg)' }}
      >
        {category.emoji}
      </div>
      <Stack gap="2" align="center">
        <Heading level={2}>생성 중...</Heading>
        <Text color="secondary" className="text-center max-w-sm">
          <strong style={{ color: 'var(--text-primary)' }}>{topic}</strong> 영상을 생성하고 있습니다.
          <br />대시보드/작업 목록에서 진행 상태를 확인하세요.
        </Text>
      </Stack>
      <Box padding="4" surface="overlay" rounded="loose" className="w-full max-w-md">
        <Stack gap="2">
          {['스크립트 생성', '메타데이터 생성', 'TTS 음성 생성', '이미지 수집', 'Remotion 렌더링', '썸네일 생성'].map((step, i) => (
            <Stack key={step} direction="row" gap="2" align="center">
              <div
                className="w-4 h-4 rounded-full flex items-center justify-center text-xs"
                style={{
                  background: i === 0 ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
                  color: i === 0 ? 'var(--text-inverse)' : 'var(--text-disabled)',
                  border: `1px solid ${i === 0 ? 'var(--interactive-primary)' : 'var(--border-default)'}`,
                }}
              />
              <Text size="sm" color={i === 0 ? 'primary' : 'disabled'}>{step}</Text>
            </Stack>
          ))}
        </Stack>
      </Box>
      <Link
        href="/"
        className="text-sm underline"
        style={{ color: 'var(--text-brand)' }}
      >
        대시보드로 돌아가기
      </Link>
    </Stack>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function GeneratePage() {
  const [step, setStep] = useState<Step>('category')
  const [category, setCategory] = useState<Category | null>(null)
  const [topic, setTopic] = useState<string | null>(null)
  const [topicOptions, setTopicOptions] = useState<TopicOption[]>([])
  const [topicLoading, setTopicLoading] = useState(false)
  const [topicError, setTopicError] = useState<string | null>(null)
  const [options, setOptions] = useState<GenerateOptions>({
    type: 'shorts',
    language: 'ko',
    tts: 'edge-tts',
    imageStyle: 0,
    renderMode: 'auto',
  })
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadTopics(categoryId: number) {
    setTopicLoading(true)
    setTopicError(null)
    try {
      const res = await fetch(`/api/topics?categoryId=${categoryId}`)
      if (!res.ok) {
        setTopicOptions([])
        setTopicError('주제 목록을 불러오지 못했습니다. 다시 시도하세요.')
        return
      }
      const data = await res.json() as { topics?: TopicOption[] }
      const topics = Array.isArray(data.topics) ? data.topics : []
      if (topics.length === 0) {
        setTopicOptions([])
        setTopicError('생성 가능한 주제가 없습니다. 다시 시도하세요.')
        return
      }
      setTopicOptions(topics)
    } catch {
      setTopicOptions([])
      setTopicError('주제 API 연결에 실패했습니다.')
    } finally {
      setTopicLoading(false)
    }
  }

  async function handleStart() {
    if (!category || !topic) return
    setError(null)
    setRunning(true)
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categoryId: category.id,
          topic,
          type: options.type,
          language: options.language,
          tts: options.tts,
          imageStyle: options.imageStyle,
          renderMode: options.renderMode,
        }),
      })

      if (!res.ok) {
        setRunning(false)
        setError('파이프라인 시작에 실패했습니다. 설정(.env)과 로그를 확인하세요.')
      }
    } catch {
      setRunning(false)
      setError('서버 연결에 실패했습니다. 잠시 후 다시 시도하세요.')
    }
  }

  if (running && category && topic) {
    return (
      <div className="flex flex-col flex-1" style={{ background: 'var(--surface-default)' }}>
        <header className="border-b" style={{ background: 'var(--surface-raised)', borderColor: 'var(--border-default)' }}>
          <Container>
            <div className="flex items-center gap-3 py-4">
              <Link href="/" className="text-sm" style={{ color: 'var(--text-brand)' }}>← 대시보드</Link>
              <Text size="sm" color="tertiary">/</Text>
              <Text size="sm" color="secondary">영상 생성</Text>
            </div>
          </Container>
        </header>
        <main className="flex-1 py-8">
          <Container size="md">
            <RunningState category={category} topic={topic} />
          </Container>
        </main>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1" style={{ background: 'var(--surface-default)' }}>
      {/* Header */}
      <header className="border-b" style={{ background: 'var(--surface-raised)', borderColor: 'var(--border-default)' }}>
        <Container>
          <div className="flex items-center gap-3 py-4">
            <Link href="/" className="text-sm" style={{ color: 'var(--text-brand)' }}>← 대시보드</Link>
            <Text size="sm" color="tertiary">/</Text>
            <Text size="sm" color="secondary">영상 생성</Text>
          </div>
        </Container>
      </header>

      {/* Step Bar */}
      <div className="border-b" style={{ background: 'var(--surface-raised)', borderColor: 'var(--border-subtle)' }}>
        <Container>
          <div className="py-4">
            <StepBar current={step} />
          </div>
        </Container>
      </div>

      {/* Main content */}
      <main className="flex-1 py-8">
        <Container size="md">
          {error && (
            <Box padding="3" surface="raised" rounded="loose" border className="mb-4">
              <Text size="sm" style={{ color: 'var(--state-danger)' }}>{error}</Text>
            </Box>
          )}

          {step === 'category' && (
            <CategoryStep
              onSelect={(cat) => {
                setCategory(cat)
                setTopic(null)
                setTopicOptions([])
                setTopicError(null)
                setStep('topic')
                void loadTopics(cat.id)
              }}
            />
          )}

          {step === 'topic' && category && (
            <TopicStep
              category={category}
              topics={topicOptions}
              loading={topicLoading}
              error={topicError}
              onRetry={() => void loadTopics(category.id)}
              onSelect={(t) => {
                setTopic(t)
                setStep('options')
              }}
              onBack={() => setStep('category')}
            />
          )}

          {step === 'options' && (
            <OptionsStep
              options={options}
              onChange={(o) => setOptions(prev => ({ ...prev, ...o }))}
              onNext={() => setStep('confirm')}
              onBack={() => setStep('topic')}
            />
          )}

          {step === 'confirm' && category && topic && (
            <ConfirmStep
              category={category}
              topic={topic}
              options={options}
              onStart={handleStart}
              onBack={() => setStep('options')}
            />
          )}
        </Container>
      </main>
    </div>
  )
}
