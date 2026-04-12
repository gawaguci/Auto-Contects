'use client'

import { useEffect, useState } from 'react'
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

interface PromptInfo {
  system: string
  template_file: string
  template_text: string
  rendered_prompt: string
}

interface ScriptSceneDraft {
  index: number
  duration: number
  narration: string
  subtitle: string
  imagePrompt: string
  bgColor: string
  videoQuery: string
}

interface ScriptDraft {
  version: 'shorts' | 'longform'
  title: string
  category: string
  totalDuration: number
  cta: string
  scenes: ScriptSceneDraft[]
}

interface GenerateOptions {
  type: 'shorts' | 'longform'
  language: 'ko' | 'en'
  tts: 'edge-tts' | 'elevenlabs' | 'typecast'
  imageStyle: number
  renderMode: 'auto' | 'studio' | 'capcut'
  playbackSpeed: 30 | 20 | 15 | 10 | 0 | -10 | -20
}

interface JobMonitor {
  id: string
  pid: number | null
  status: 'running' | 'completed' | 'failed' | 'stopped'
  step: string | null
  error: string | null
  progressCurrent: number | null
  progressTotal: number | null
  mtime: number
}

const RUNNING_STEPS = [
  '스크립트 생성',
  'TTS 음성 생성',
  '이미지 생성',
  '렌더링',
  '캡컷 프로젝트 생성',
  '캡컷 실행',
]

const RUNNING_STEP_KEYWORDS: string[][] = [
  ['스크립트 생성'],
  ['TTS 음성 생성'],
  ['이미지 생성', '캡컷용 이미지/클립 생성', '이미지 수집'],
  ['렌더링', '영상 조합'],
  ['캡컷 프로젝트 생성'],
  ['캡컷 실행'],
]

function findCurrentStepIndex(step: string | null, progressCurrent: number | null): number {
  if (step) {
    const idx = RUNNING_STEP_KEYWORDS.findIndex((keywords) =>
      keywords.some((label) => step.includes(label)),
    )
    if (idx >= 0) return idx
  }

  if (typeof progressCurrent === 'number' && Number.isFinite(progressCurrent)) {
    const bounded = Math.min(Math.max(progressCurrent, 0), RUNNING_STEPS.length - 1)
    return bounded
  }

  return 0
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

const PLAYBACK_SPEED_OPTIONS: Array<30 | 20 | 15 | 10 | 0 | -10 | -20> = [30, 20, 15, 10, 0, -10, -20]

function formatPlaybackSpeed(value: number): string {
  return `${value > 0 ? '+' : ''}${value}%`
}

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
            className="group text-left p-4 rounded-xl border cursor-pointer transition-all duration-150 hover:-translate-y-0.5 hover:shadow-lg hover:border-[var(--border-focus)] hover:bg-[var(--surface-overlay)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--interactive-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface-default)]"
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
  topicPrompt,
  onRetry,
  onSelect,
  onBack,
}: {
  category: Category
  topics: TopicOption[]
  loading: boolean
  error: string | null
  topicPrompt: PromptInfo | null
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
              className="text-left p-4 rounded-lg border cursor-pointer transition-all duration-150 hover:-translate-y-px hover:shadow-md hover:border-[var(--border-focus)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--interactive-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface-default)]"
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

      {topicPrompt && (
        <Box padding="3" surface="raised" rounded="loose" border>
          <Stack gap="2">
            <Text size="sm" weight="medium">주제 선정 프롬프트 템플릿</Text>
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--text-brand)' }}>템플릿 보기 ({topicPrompt.template_file})</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>{topicPrompt.template_text}</pre>
            </details>
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--text-brand)' }}>AI 전달 프롬프트 보기</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>{topicPrompt.rendered_prompt}</pre>
            </details>
          </Stack>
        </Box>
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
      className="px-4 py-2 rounded-lg text-sm font-medium border cursor-pointer transition-all duration-150 hover:-translate-y-px hover:shadow-sm hover:border-[var(--border-focus)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--interactive-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface-default)]"
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

      {/* Playback Speed */}
      <Box>
        <Stack gap="2">
          <Label>영상 재생 속도</Label>
          {options.renderMode === 'capcut' ? (
            <Text size="sm" color="tertiary">캡컷 프로젝트 모드에서는 재생 속도 설정이 적용되지 않습니다.</Text>
          ) : (
            <Stack direction="row" gap="2">
              {PLAYBACK_SPEED_OPTIONS.map((speed) => (
                <OptionButton
                  key={speed}
                  label={formatPlaybackSpeed(speed)}
                  selected={options.playbackSpeed === speed}
                  onClick={() => onChange({ playbackSpeed: speed })}
                />
              ))}
            </Stack>
          )}
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
  scriptDraft,
  scriptLoading,
  scriptError,
  topicPrompt,
  scriptPrompt,
  onScriptReload,
  onScriptChange,
  onStart,
  onBack,
}: {
  category: Category
  topic: string
  options: GenerateOptions
  scriptDraft: ScriptDraft | null
  scriptLoading: boolean
  scriptError: string | null
  topicPrompt: PromptInfo | null
  scriptPrompt: PromptInfo | null
  onScriptReload: () => void
  onScriptChange: (next: ScriptDraft) => void
  onStart: () => void
  onBack: () => void
}) {
  const typeLabel = options.type === 'shorts' ? '쇼츠 (90초)' : '롱폼 (10분)'
  const langLabel = options.language === 'ko' ? '한국어' : '영어'
  const ttsLabel = options.tts === 'edge-tts' ? 'Edge-TTS (무료)' : options.tts === 'elevenlabs' ? 'ElevenLabs' : 'Typecast'
  const styleLabel = IMAGE_STYLES.find(s => s.id === options.imageStyle)?.name ?? '화풍 없음'
  const renderLabel = options.renderMode === 'auto' ? '자동 렌더링' : options.renderMode === 'studio' ? 'Remotion Studio' : '캡컷 프로젝트'
  const playbackSpeedLabel = options.renderMode === 'capcut' ? '해당 없음 (캡컷)' : formatPlaybackSpeed(options.playbackSpeed)

  const rows = [
    { label: '카테고리', value: `${category.emoji} ${category.name}` },
    { label: '주제', value: topic },
    { label: '유형', value: typeLabel },
    { label: '언어', value: langLabel },
    { label: 'TTS', value: ttsLabel },
    { label: '이미지 스타일', value: styleLabel },
    { label: '렌더링', value: renderLabel },
    { label: '재생 속도', value: playbackSpeedLabel },
  ]

  const canStart = !scriptLoading && !!scriptDraft && scriptDraft.scenes.length > 0

  const updateScene = (sceneIndex: number, patch: Partial<ScriptSceneDraft>) => {
    if (!scriptDraft) return
    onScriptChange({
      ...scriptDraft,
      scenes: scriptDraft.scenes.map((scene) =>
        scene.index === sceneIndex ? { ...scene, ...patch } : scene,
      ),
    })
  }

  return (
    <Stack gap="5">
      <Stack gap="1">
        <Heading level={2}>생성 확인</Heading>
        <Text color="secondary">설정을 확인하고, 생성 전 스토리/자막을 검토 및 편집하세요.</Text>
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

      <Box padding="4" surface="raised" rounded="loose" border>
        <Stack gap="2">
          <Text size="sm" weight="medium">프롬프트 템플릿</Text>
          {topicPrompt && (
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--text-brand)' }}>주제 리스트 프롬프트 ({topicPrompt.template_file})</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>{topicPrompt.template_text}</pre>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-tertiary)' }}>{topicPrompt.rendered_prompt}</pre>
            </details>
          )}
          {scriptPrompt && (
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--text-brand)' }}>스토리/자막 생성 프롬프트 ({scriptPrompt.template_file})</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>{scriptPrompt.template_text}</pre>
              <pre className="text-xs mt-2 whitespace-pre-wrap" style={{ color: 'var(--text-tertiary)' }}>{scriptPrompt.rendered_prompt}</pre>
            </details>
          )}
        </Stack>
      </Box>

      <Box padding="4" surface="raised" rounded="loose" border>
        <Stack gap="3">
          <Stack direction="row" gap="2" align="center">
            <Text size="sm" weight="medium">씬별 스토리 / 자막 편집</Text>
            <button
              onClick={onScriptReload}
              className="px-3 py-1 rounded-lg text-xs font-medium border"
              style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}
            >
              다시 생성
            </button>
          </Stack>

          {scriptLoading && <Text size="sm" color="secondary">스크립트/자막 초안을 생성하는 중입니다...</Text>}
          {scriptError && <Text size="sm" style={{ color: 'var(--state-danger)' }}>{scriptError}</Text>}

          {scriptDraft && (
            <Stack gap="3">
              <div>
                <Label>제목</Label>
                <input
                  value={scriptDraft.title}
                  onChange={(e) => onScriptChange({ ...scriptDraft, title: e.target.value })}
                  className="w-full mt-1 px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border-default)', background: 'var(--surface-default)', color: 'var(--text-primary)' }}
                />
              </div>

              <div>
                <Label>CTA</Label>
                <input
                  value={scriptDraft.cta ?? ''}
                  onChange={(e) => onScriptChange({ ...scriptDraft, cta: e.target.value })}
                  className="w-full mt-1 px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border-default)', background: 'var(--surface-default)', color: 'var(--text-primary)' }}
                />
              </div>

              <Stack gap="2">
                {scriptDraft.scenes.map((scene) => (
                  <Box key={scene.index} padding="3" surface="overlay" rounded="default" border>
                    <Stack gap="2">
                      <Text size="sm" weight="medium">씬 {scene.index}</Text>
                      <div>
                        <Label>스토리(나레이션)</Label>
                        <textarea
                          value={scene.narration}
                          onChange={(e) => updateScene(scene.index, { narration: e.target.value })}
                          rows={3}
                          className="w-full mt-1 px-3 py-2 rounded-lg border text-sm"
                          style={{ borderColor: 'var(--border-default)', background: 'var(--surface-default)', color: 'var(--text-primary)' }}
                        />
                      </div>
                      <div>
                        <Label>자막</Label>
                        <input
                          value={scene.subtitle}
                          onChange={(e) => updateScene(scene.index, { subtitle: e.target.value })}
                          className="w-full mt-1 px-3 py-2 rounded-lg border text-sm"
                          style={{ borderColor: 'var(--border-default)', background: 'var(--surface-default)', color: 'var(--text-primary)' }}
                        />
                      </div>
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </Stack>
          )}
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
          disabled={!canStart}
          className="flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold"
          style={{
            background: canStart ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
            color: canStart ? 'var(--text-inverse)' : 'var(--text-disabled)',
            cursor: canStart ? 'pointer' : 'not-allowed',
          }}
        >
          ▶ 영상 생성 시작
        </button>
      </Stack>
    </Stack>
  )
}

// ── Running State ─────────────────────────────────────────────────────────────

function RunningState({ category, topic, job }: { category: Category; topic: string; job: JobMonitor | null }) {
  const status = job?.status ?? 'running'
  const isRunning = status === 'running'

  const statusTitle = status === 'completed'
    ? '생성 완료'
    : status === 'failed'
      ? '생성 실패'
      : status === 'stopped'
        ? '생성 중단'
        : '생성 중...'

  const statusTone = status === 'completed'
    ? { bg: 'var(--state-success-bg)', fg: 'var(--state-success)' }
    : status === 'failed'
      ? { bg: 'var(--state-danger-bg)', fg: 'var(--state-danger)' }
      : status === 'stopped'
        ? { bg: 'var(--surface-overlay)', fg: 'var(--text-secondary)' }
        : { bg: 'var(--state-info-bg)', fg: 'var(--state-info)' }

  const currentIdx = findCurrentStepIndex(job?.step ?? null, job?.progressCurrent ?? null)

  return (
    <Stack gap="6" align="center" className="py-12">
      <div
        className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl ${isRunning ? 'animate-pulse' : ''}`}
        style={{ background: 'var(--interactive-primary-bg)' }}
      >
        {category.emoji}
      </div>

      <Stack gap="2" align="center">
        <Heading level={2}>{statusTitle}</Heading>
        <Text color="secondary" className="text-center max-w-md">
          <strong style={{ color: 'var(--text-primary)' }}>{topic}</strong>
          {status === 'completed' && ' 영상 생성이 완료되었습니다.'}
          {status === 'failed' && ' 영상 생성이 실패했습니다.'}
          {status === 'stopped' && ' 영상 생성이 중단되었습니다.'}
          {status === 'running' && ' 영상을 생성하고 있습니다.'}
        </Text>
      </Stack>

      <Box padding="4" surface="raised" rounded="loose" border className="w-full max-w-md">
        <Stack gap="2">
          <Stack direction="row" gap="2" align="center">
            <span
              className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              style={{ background: statusTone.bg, color: statusTone.fg }}
            >
              {status === 'running' ? '진행중' : status === 'completed' ? '완료' : status === 'failed' ? '실패' : '중단됨'}
            </span>
            {job?.id && <Text size="xs" color="tertiary">Job: {job.id}</Text>}
          </Stack>

          {job?.step && <Text size="sm" color="secondary">현재 단계: {job.step}</Text>}

          {job && job.progressCurrent !== null && job.progressTotal !== null && (
            <Text size="xs" color="tertiary">진행률: {job.progressCurrent} / {job.progressTotal}</Text>
          )}
        </Stack>
      </Box>

      {status === 'failed' && job?.error && (
        <Box padding="3" surface="raised" rounded="loose" border className="w-full max-w-md">
          <Text size="sm" style={{ color: 'var(--state-danger)' }}>
            오류: {job.error}
          </Text>
        </Box>
      )}

      <Box padding="4" surface="overlay" rounded="loose" className="w-full max-w-md">
        <Stack gap="2">
          {RUNNING_STEPS.map((step, i) => {
            const done = status === 'completed' || i < currentIdx
            const active = status !== 'completed' && i === currentIdx
            return (
              <Stack key={step} direction="row" gap="2" align="center">
                <div
                  className="w-4 h-4 rounded-full flex items-center justify-center text-xs"
                  style={{
                    background: done || active ? 'var(--interactive-primary)' : 'var(--surface-overlay)',
                    color: done || active ? 'var(--text-inverse)' : 'var(--text-disabled)',
                    border: `1px solid ${done || active ? 'var(--interactive-primary)' : 'var(--border-default)'}`,
                  }}
                />
                <Text size="sm" color={done || active ? 'primary' : 'disabled'}>{step}</Text>
              </Stack>
            )
          })}
        </Stack>
      </Box>

      <Link href="/jobs" className="text-sm underline" style={{ color: 'var(--text-brand)' }}>
        작업 목록으로 이동
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
  const [topicPromptInfo, setTopicPromptInfo] = useState<PromptInfo | null>(null)
  const [scriptDraft, setScriptDraft] = useState<ScriptDraft | null>(null)
  const [scriptPromptInfo, setScriptPromptInfo] = useState<PromptInfo | null>(null)
  const [scriptLoading, setScriptLoading] = useState(false)
  const [scriptError, setScriptError] = useState<string | null>(null)
  const [options, setOptions] = useState<GenerateOptions>({
    type: 'shorts',
    language: 'ko',
    tts: 'edge-tts',
    imageStyle: 0,
    renderMode: 'auto',
    playbackSpeed: 0,
  })
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null)
  const [runPid, setRunPid] = useState<number | null>(null)
  const [latestJob, setLatestJob] = useState<JobMonitor | null>(null)

  useEffect(() => {
    if (!running) return

    let mounted = true

    const pollLatestJob = async () => {
      try {
        const res = await fetch('/api/jobs/latest', { cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json() as { job?: JobMonitor | null }
        if (!mounted) return

        const job = data.job ?? null
        if (!job) return

        if (runPid !== null && job.pid !== runPid) {
          return
        }

        if (runStartedAt && typeof job.mtime === 'number' && job.mtime + 3000 < runStartedAt) {
          return
        }

        setLatestJob(job)
      } catch {
        // 폴링 실패는 무시하고 다음 주기 재시도
      }
    }

    void pollLatestJob()
    const timer = setInterval(() => { void pollLatestJob() }, 2000)

    return () => {
      mounted = false
      clearInterval(timer)
    }
  }, [running, runPid, runStartedAt])

  async function loadTopics(categoryId: number) {
    setTopicLoading(true)
    setTopicError(null)
    setTopicPromptInfo(null)
    try {
      const res = await fetch(`/api/topics?categoryId=${categoryId}`)
      if (!res.ok) {
        setTopicOptions([])
        setTopicError('주제 목록을 불러오지 못했습니다. 다시 시도하세요.')
        return
      }
      const data = await res.json() as { topics?: TopicOption[]; prompt?: PromptInfo | null }
      const topics = Array.isArray(data.topics) ? data.topics : []
      if (topics.length === 0) {
        setTopicOptions([])
        setTopicError('생성 가능한 주제가 없습니다. 다시 시도하세요.')
        return
      }
      setTopicOptions(topics)
      setTopicPromptInfo(data.prompt ?? null)
    } catch {
      setTopicOptions([])
      setTopicPromptInfo(null)
      setTopicError('주제 API 연결에 실패했습니다.')
    } finally {
      setTopicLoading(false)
    }
  }

  async function loadScriptPreview() {
    if (!category || !topic) return

    setScriptLoading(true)
    setScriptError(null)
    try {
      const res = await fetch('/api/script/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categoryId: category.id,
          topic,
          type: options.type,
          language: options.language,
        }),
      })

      const data = await res.json() as { script?: ScriptDraft; prompt?: PromptInfo | null; error?: string }
      if (!res.ok || !data.script || !Array.isArray(data.script.scenes)) {
        setScriptDraft(null)
        setScriptPromptInfo(null)
        setScriptError(data.error ?? '스크립트 프리뷰를 불러오지 못했습니다.')
        return
      }

      const normalizedScenes = data.script.scenes.map((scene, idx) => ({
        index: Number(scene.index) || (idx + 1),
        duration: Number(scene.duration) || 6,
        narration: String(scene.narration ?? ''),
        subtitle: String(scene.subtitle ?? ''),
        imagePrompt: String(scene.imagePrompt ?? ''),
        bgColor: String(scene.bgColor ?? '#101622'),
        videoQuery: String(scene.videoQuery ?? ''),
      }))

      setScriptDraft({
        ...data.script,
        cta: String(data.script.cta ?? ''),
        scenes: normalizedScenes,
      })
      setScriptPromptInfo(data.prompt ?? null)
    } catch {
      setScriptDraft(null)
      setScriptPromptInfo(null)
      setScriptError('스크립트 프리뷰 API 연결에 실패했습니다.')
    } finally {
      setScriptLoading(false)
    }
  }

  async function handleGoConfirm() {
    setStep('confirm')
    await loadScriptPreview()
  }

  async function handleStart() {
    if (!category || !topic) return
    setError(null)
    setLatestJob(null)
    setRunPid(null)
    setRunStartedAt(Date.now())
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
          playbackSpeed: options.renderMode === 'capcut' ? 0 : options.playbackSpeed,
          scriptOverride: scriptDraft ? {
            title: scriptDraft.title,
            cta: scriptDraft.cta,
            scenes: scriptDraft.scenes.map((scene) => ({
              index: scene.index,
              duration: scene.duration,
              narration: scene.narration,
              subtitle: scene.subtitle,
              imagePrompt: scene.imagePrompt,
              bgColor: scene.bgColor,
              videoQuery: scene.videoQuery,
            })),
          } : null,
        }),
      })

      const payload = await res.json().catch(() => ({})) as { pid?: number }

      if (!res.ok) {
        setRunning(false)
        setRunPid(null)
        setRunStartedAt(null)
        setError('파이프라인 시작에 실패했습니다. 설정(.env)과 로그를 확인하세요.')
        return
      }

      setRunPid(typeof payload.pid === 'number' ? payload.pid : null)
    } catch {
      setRunning(false)
      setRunPid(null)
      setRunStartedAt(null)
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
            <RunningState category={category} topic={topic} job={latestJob} />
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
                setTopicPromptInfo(null)
                setScriptDraft(null)
                setScriptPromptInfo(null)
                setScriptError(null)
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
              topicPrompt={topicPromptInfo}
              onRetry={() => void loadTopics(category.id)}
              onSelect={(t) => {
                setTopic(t)
                setScriptDraft(null)
                setScriptPromptInfo(null)
                setScriptError(null)
                setStep('options')
              }}
              onBack={() => setStep('category')}
            />
          )}

          {step === 'options' && (
            <OptionsStep
              options={options}
              onChange={(o) => {
                setOptions(prev => ({ ...prev, ...o }))
                setScriptDraft(null)
                setScriptPromptInfo(null)
                setScriptError(null)
              }}
              onNext={() => { void handleGoConfirm() }}
              onBack={() => setStep('topic')}
            />
          )}

          {step === 'confirm' && category && topic && (
            <ConfirmStep
              category={category}
              topic={topic}
              options={options}
              scriptDraft={scriptDraft}
              scriptLoading={scriptLoading}
              scriptError={scriptError}
              topicPrompt={topicPromptInfo}
              scriptPrompt={scriptPromptInfo}
              onScriptReload={() => { void loadScriptPreview() }}
              onScriptChange={setScriptDraft}
              onStart={handleStart}
              onBack={() => setStep('options')}
            />
          )}
        </Container>
      </main>
    </div>
  )
}

