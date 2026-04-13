import React, { useMemo } from 'react'
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion'

type Role = 'hook' | 'problem' | 'numbered' | 'stat' | 'solution' | 'closing' | ''

type Scene = {
  index: number
  duration: number
  narration: string
  subtitle: string
  imagePrompt: string
  bgColor: string
  bgImage: string
  audioFile: string
  role: Role
}

type SubtitleItem = {
  start: number
  end: number
  text: string
}

export type RemotionInput = {
  version: string
  title: string
  category: string
  categoryEmoji: string
  categoryId: number
  totalDuration: number
  cta: string
  fps: number
  width: number
  height: number
  fullAudioFile: string
  scenes: Scene[]
  subtitles: SubtitleItem[]
}

const toFrames = (s: number, fps: number) => Math.max(1, Math.ceil(s * fps))

const sceneOffsets = (scenes: Scene[], fps: number) => {
  let cursor = 0
  return scenes.map((scene) => {
    const dur = toFrames(scene.duration, fps)
    const start = cursor
    cursor += dur
    return { start, end: cursor }
  })
}

interface SceneInfo {
  scene: Scene | null
  localFrame: number
  sceneDuration: number
}

const getSceneInfo = (frame: number, scenes: Scene[], fps: number): SceneInfo => {
  const offsets = sceneOffsets(scenes, fps)
  for (let i = 0; i < offsets.length; i++) {
    const { start, end } = offsets[i]
    if (frame >= start && frame < end) {
      return { scene: scenes[i], localFrame: frame - start, sceneDuration: end - start }
    }
  }
  const last = offsets[offsets.length - 1]
  return {
    scene: scenes[scenes.length - 1] ?? null,
    localFrame: last ? frame - last.start : 0,
    sceneDuration: last ? last.end - last.start : 1,
  }
}

const getSrt = (sec: number, subs: SubtitleItem[]) =>
  subs.find((s) => sec >= s.start && sec <= s.end)?.text ?? null

// ── 역할별 강조 색상 ────────────────────────────────────────────────────
const ACCENT: Record<string, string> = {
  hook:     '#FF3B30',
  problem:  '#c77dff',
  numbered: '#4cc9f0',
  stat:     '#FFD60A',
  solution: '#00C853',
  closing:  '#64D2FF',
  '':       '#ffffff',
}

// ── 롱폼 플로팅 키워드 (hook/problem/solution 씬 배경에 감정어 부유)
// 레퍼런스 15번: "해방감", "불안감" 등 캐릭터 주변에 반투명으로 떠다님
const FLOATING_WORDS: Record<string, string[]> = {
  hook:     ['충격', '반전', '진실'],
  problem:  ['불안감', '위기', '변화'],
  solution: ['해결책', '기회', '전략'],
}

const hasNum = (t: string) => /\d/.test(t)

const parseNum = (t: string) => {
  const m = t.match(/^(.*?)(\d+\.?\d*)(.*?)$/)
  return m ? { pre: m[1], num: parseFloat(m[2]), suf: m[3] } : null
}

// subtitle에서 핵심 키워드 추출 (레이블 박스용)
const extractKeyword = (subtitle: string): string => {
  const cleaned = subtitle.replace(/[。.!?！？,，]/g, '').trim()
  const words = cleaned.split(/\s+/)
  const numWord = words.find(w => /\d/.test(w))
  if (numWord) return numWord
  return words[0] ?? cleaned.slice(0, 6)
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [공통] 씬 전환 — 왼쪽 엣지 와이프 플래시
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const WipeEdge: React.FC<{ localFrame: number; fps: number }> = ({ localFrame, fps }) => {
  const EDGE_DUR = Math.floor(fps * 0.14)
  if (localFrame > EDGE_DUR) return null
  const opacity = interpolate(localFrame, [0, 2, EDGE_DUR], [1, 0.7, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  })
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 10,
        background: 'linear-gradient(to right, rgba(255,255,255,0.95), transparent)',
        opacity,
      }} />
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [공통] Ken Burns 배경
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const KenBurns: React.FC<{
  bgImage: string; bgColor: string
  localFrame: number; sceneDuration: number; role: Role
}> = ({ bgImage, bgColor, localFrame, sceneDuration, role }) => {
  const zoomOut = role === 'solution' || role === 'closing'
  const scale = interpolate(localFrame, [0, sceneDuration],
    zoomOut ? [1.08, 1.0] : [1.0, 1.08],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  )
  const shakeX = (role === 'hook' || role === 'problem')
    ? interpolate(Math.sin(localFrame * 0.35), [-1, 1], [-3, 3])
    : 0
  return (
    <AbsoluteFill style={{ backgroundColor: bgColor, overflow: 'hidden' }}>
      {bgImage && (
        <Img
          src={staticFile(bgImage)}
          style={{
            width: '100%', height: '100%', objectFit: 'cover',
            transform: `scale(${scale}) translateX(${shakeX}px)`,
            transformOrigin: 'center center',
          }}
        />
      )}
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [공통] 그라디언트 오버레이
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const Gradient: React.FC<{ role: Role; isShorts: boolean; localFrame: number; fps: number }> = ({ role, isShorts, localFrame, fps }) => {
  const fadeIn = interpolate(localFrame, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  })
  // 숏폼: 상단도 어둡게 (제목 배너 가독성)
  const topStr = isShorts ? 'rgba(0,0,0,0.65)' : 'rgba(0,0,0,0.0)'
  const bottomStr = role === 'closing' ? 'rgba(0,0,0,0.45)' : 'rgba(0,0,0,0.80)'
  const midStr = role === 'closing' ? 'rgba(0,0,0,0.08)' : 'rgba(0,0,0,0.28)'

  return (
    <>
      <AbsoluteFill style={{
        background: `linear-gradient(to top, ${bottomStr} 0%, ${midStr} 45%, ${topStr} 100%)`,
        opacity: fadeIn, pointerEvents: 'none',
      }} />
    </>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [숏폼 전용] 상단 고정 제목 배너
// 레퍼런스 398: 영상 내내 상단에 굵은 컬러 텍스트로 제목 2줄 고정
// 예) "한국 200명짜리 회사가 / 일본 20년 독점에 칼을 꽂았다"
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const ShortsTitleBanner: React.FC<{
  title: string; localFrame: number; fps: number
  width: number
}> = ({ title, localFrame, fps, width }) => {
  // 씬 시작 후 페이드인
  const opacity = interpolate(localFrame, [0, fps * 0.2], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  })

  // 제목을 최대 2줄로 분할 (중간쯤에서 줄바꿈)
  const words = title.split(' ')
  const mid = Math.ceil(words.length / 2)
  const line1 = words.slice(0, mid).join(' ')
  const line2 = words.slice(mid).join(' ')

  const fontSize = width < 800 ? 32 : 28

  return (
    <AbsoluteFill style={{
      justifyContent: 'flex-start', alignItems: 'center',
      paddingTop: 36,
      pointerEvents: 'none',
    }}>
      <div style={{
        opacity,
        textAlign: 'center',
        display: 'flex', flexDirection: 'column', gap: 2,
      }}>
        {[line1, line2].filter(Boolean).map((line, i) => (
          <div key={i} style={{
            color: i === 0 ? '#00FF88' : '#FFFFFF',
            fontSize,
            fontWeight: 900,
            lineHeight: 1.25,
            letterSpacing: '-0.02em',
            textShadow: [
              '2px 2px 0 #000', '-2px 2px 0 #000',
              '2px -2px 0 #000', '-2px -2px 0 #000',
              '0 4px 20px rgba(0,0,0,0.9)',
            ].join(', '),
            wordBreak: 'keep-all',
          }}>
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [롱폼 전용] 좌상단 맥락 레이블 박스 + numbered 원형 배지
// 레퍼런스 14·15번: "2036년 노동시장 변화", "금융감독원", stat 키워드 등
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const ContextLabel: React.FC<{
  role: Role; subtitle: string; index: number
  localFrame: number; fps: number; isLongform: boolean
}> = ({ role, subtitle, index, localFrame, fps, isLongform }) => {
  const delay = Math.floor(fps * 0.08)
  const prog = spring({
    frame: localFrame - delay, fps,
    config: { damping: 22, stiffness: 280, mass: 0.45 },
  })
  const tx = interpolate(prog, [0, 1], [-120, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  const opacity = interpolate(prog, [0, 0.5, 1], [0, 1, 1])
  const accent = ACCENT[role] || '#fff'
  const pad = isLongform ? '52px 44px 0' : '68px 52px 0'
  const circleSize = isLongform ? 76 : 96

  if (role === 'numbered') {
    return (
      <AbsoluteFill style={{
        justifyContent: 'flex-start', alignItems: 'flex-start',
        padding: pad, boxSizing: 'border-box', pointerEvents: 'none',
      }}>
        <div style={{
          width: circleSize, height: circleSize, borderRadius: '50%',
          backgroundColor: accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 900, fontSize: circleSize * 0.42, color: '#000',
          opacity, transform: `translateX(${tx}px)`,
          boxShadow: `0 0 28px ${accent}99, 0 4px 16px rgba(0,0,0,0.6)`,
        }}>
          {index}
        </div>
      </AbsoluteFill>
    )
  }

  // problem / stat: 핵심 키워드 레이블 박스
  const keyword = extractKeyword(subtitle)
  const fontSize = isLongform ? 18 : 24

  return (
    <AbsoluteFill style={{
      justifyContent: 'flex-start', alignItems: 'flex-start',
      padding: pad, boxSizing: 'border-box', pointerEvents: 'none',
    }}>
      <div style={{
        backgroundColor: 'rgba(0,0,0,0.78)',
        border: `2px solid ${accent}`,
        borderRadius: isLongform ? 8 : 10,
        padding: isLongform ? '8px 18px' : '10px 22px',
        opacity, transform: `translateX(${tx}px)`,
        boxShadow: `0 2px 16px rgba(0,0,0,0.7)`,
      }}>
        <span style={{
          color: accent, fontWeight: 800, fontSize,
          letterSpacing: '0.02em',
          textShadow: `0 0 12px ${accent}88`,
        }}>
          {keyword}
        </span>
      </div>
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [롱폼 전용] 플로팅 감정 키워드
// 레퍼런스 15번: "해방감", "불안감" 반투명으로 좌우에 떠다님
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const FloatingWords: React.FC<{
  role: Role
  localFrame: number; fps: number; sceneDuration: number; isLongform: boolean
}> = ({ role, localFrame, fps, sceneDuration, isLongform }) => {
  const words = FLOATING_WORDS[role]
  if (!words) return null
  const accent = ACCENT[role] || '#fff'
  const fontSize = isLongform ? 22 : 30

  const positions = [
    { left: '6%', top: '20%' },
    { left: '5%', top: '46%' },
    { right: '5%', top: '24%' },
  ]

  return (
    <>
      {words.slice(0, 3).map((word, i) => {
        const delay = Math.floor(fps * (0.2 + i * 0.15))
        const prog = spring({
          frame: localFrame - delay, fps,
          config: { damping: 20, stiffness: 120, mass: 1.2 },
        })
        const fadeOut = interpolate(
          localFrame,
          [sceneDuration * 0.75, sceneDuration * 0.95],
          [1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        )
        const opacity = interpolate(prog, [0, 1], [0, 0.52]) * fadeOut
        const ty = interpolate(prog, [0, 1], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })

        return (
          <AbsoluteFill key={word} style={{ pointerEvents: 'none' }}>
            <div style={{
              position: 'absolute', ...positions[i],
              color: accent, fontSize, fontWeight: 800,
              opacity, transform: `translateY(${ty}px)`,
              letterSpacing: '0.04em',
              textShadow: `0 2px 12px rgba(0,0,0,0.8)`,
              whiteSpace: 'nowrap',
            }}>
              {word}
            </div>
          </AbsoluteFill>
        )
      })}
    </>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [롱폼 전용] StatBox — 수치 강조 박스 (stat/hook 씬, 수치 있을 때)
// 레퍼런스 14·15번: 어두운 박스 + 컬러 테두리 + 카운트업
// 숏폼은 수치가 이미지에 baked되어 있으므로 Remotion StatBox 불필요
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const StatBox: React.FC<{
  text: string; role: Role
  localFrame: number; fps: number; sceneDuration: number; isLongform: boolean
}> = ({ text, role, localFrame, fps, sceneDuration, isLongform }) => {
  const parsed = parseNum(text)
  const isNeg = text.includes('-') || text.includes('하락') || text.includes('감소') || text.includes('손실')
  const accent = role === 'stat'
    ? (isNeg ? '#FF3B30' : '#FFD60A')
    : ACCENT[role] || '#FFD60A'

  const countProg = interpolate(
    localFrame, [fps * 0.12, sceneDuration * 0.82], [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  )
  const eased = 1 - Math.pow(1 - countProg, 3)
  const displayNum = parsed
    ? (parsed.num * eased).toFixed(parsed.num % 1 !== 0 ? 1 : 0)
    : null

  const prog = spring({ frame: localFrame, fps, config: { damping: 14, stiffness: 180, mass: 0.7 } })
  const scale = interpolate(prog, [0, 1], [0.6, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  const opacity = interpolate(prog, [0, 0.6, 1], [0, 1, 1])

  const numSize = isLongform ? 88 : 120
  const unitSize = isLongform ? 40 : 56
  const padV = isLongform ? 16 : 22
  const padH = isLongform ? 36 : 52

  return (
    <AbsoluteFill style={{
      justifyContent: 'center', alignItems: 'center',
      pointerEvents: 'none',
      paddingBottom: isLongform ? '110px' : '190px',
    }}>
      <div style={{
        opacity, transform: `scale(${scale})`,
        backgroundColor: 'rgba(0,0,0,0.75)',
        border: `3px solid ${accent}`,
        borderRadius: isLongform ? 16 : 20,
        padding: `${padV}px ${padH}px`,
        display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 4,
        boxShadow: `0 0 40px ${accent}55, 0 8px 32px rgba(0,0,0,0.8)`,
      }}>
        {parsed && displayNum !== null ? (
          <>
            {parsed.pre && (
              <span style={{ color: '#fff', fontSize: unitSize, fontWeight: 700, lineHeight: 1 }}>
                {parsed.pre}
              </span>
            )}
            <span style={{
              color: accent, fontSize: numSize, fontWeight: 900, lineHeight: 1,
              textShadow: `0 0 40px ${accent}cc`,
              fontVariantNumeric: 'tabular-nums',
            }}>
              {displayNum}
            </span>
            {parsed.suf && (
              <span style={{ color: '#fff', fontSize: unitSize, fontWeight: 700, lineHeight: 1 }}>
                {parsed.suf}
              </span>
            )}
          </>
        ) : (
          <span style={{
            color: accent, fontSize: numSize * 0.65, fontWeight: 900, lineHeight: 1,
            textShadow: `0 0 40px ${accent}cc`,
          }}>
            {text}
          </span>
        )}
      </div>
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [롱폼 전용] CTA 엔딩 오버레이 (closing 씬)
// 레퍼런스 14·15번: 구독/좋아요/댓글 원형 버튼 우측 세로 배치
// 숏폼은 CTA가 이미지에 baked되어 있음
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const CtaOverlay: React.FC<{
  localFrame: number; fps: number; isLongform: boolean
}> = ({ localFrame, fps, isLongform }) => {
  const buttons = [
    { label: '구독', color: '#FF3B30', icon: '▶' },
    { label: '좋아요', color: '#FFD60A', icon: '👍' },
    { label: '댓글', color: '#00C853', icon: '💬' },
  ]
  const btnSize = isLongform ? 88 : 108
  const labelSize = isLongform ? 15 : 19
  const iconSize = isLongform ? 28 : 36

  return (
    <AbsoluteFill style={{
      justifyContent: 'flex-end', alignItems: 'flex-end',
      padding: isLongform ? '0 56px 96px 0' : '0 48px 230px 0',
      boxSizing: 'border-box', pointerEvents: 'none',
      flexDirection: 'column', gap: 18,
    }}>
      {buttons.map((btn, i) => {
        const delay = Math.floor(fps * (0.12 + i * 0.1))
        const prog = spring({
          frame: localFrame - delay, fps,
          config: { damping: 12, stiffness: 260, mass: 0.4 },
        })
        const scale = interpolate(prog, [0, 1], [0.1, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
        const opacity = interpolate(prog, [0, 0.4, 1], [0, 1, 1])
        return (
          <div key={btn.label} style={{
            opacity, transform: `scale(${scale})`,
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5,
          }}>
            <div style={{
              width: btnSize, height: btnSize, borderRadius: '50%',
              backgroundColor: btn.color,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: iconSize,
              boxShadow: `0 4px 20px rgba(0,0,0,0.6), 0 0 20px ${btn.color}88`,
              border: '3px solid rgba(255,255,255,0.3)',
            }}>
              {btn.icon}
            </div>
            <span style={{
              color: '#fff', fontSize: labelSize, fontWeight: 800,
              textShadow: '0 2px 8px rgba(0,0,0,0.9), 1px 0 0 #000, -1px 0 0 #000',
            }}>
              {btn.label}
            </span>
          </div>
        )
      })}
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// [공통] SRT 자막 — 포맷·role에 따라 스타일 3종 전환
//
// [숏폼] 모든 씬: 흰색 + 두꺼운 검은 외곽선 (배경 없음)
//          위치: 화면 하단 20% (더 아래 — 레퍼런스 398 스타일)
//
// [롱폼] 기본: 흰색 + 검은 외곽선 (배경 없음) — 레퍼런스 14·15번 기본
//        임팩트: 검은 배경 박스 + 흰 굵은 텍스트
//          → stat 씬에서 수치가 없을 때
//          → problem 씬에서 짧은 강조 문장 (18자 이하)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const SrtLine: React.FC<{
  text: string; role: Role; isImpact: boolean; isShorts: boolean
  localFrame: number; fps: number
  bottomPad: number; fontSize: number
}> = ({ text, role, isImpact, isShorts, localFrame, fps, bottomPad, fontSize }) => {
  const opacity = interpolate(localFrame, [0, fps * 0.05], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  })
  const ty = interpolate(localFrame, [0, fps * 0.07], [8, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  })

  // 숏폼 or 롱폼 기본: 흰색 + 검은 외곽선
  const outlineStyle = {
    color: '#ffffff',
    fontSize,
    fontWeight: 800,
    textAlign: 'center' as const,
    lineHeight: 1.35,
    letterSpacing: '-0.01em',
    opacity,
    transform: `translateY(${ty}px)`,
    textShadow: [
      '2px 2px 0 #000', '-2px 2px 0 #000',
      '2px -2px 0 #000', '-2px -2px 0 #000',
      '3px 0 0 #000', '-3px 0 0 #000',
      '0 3px 0 #000', '0 -3px 0 #000',
      '0 4px 16px rgba(0,0,0,0.95)',
    ].join(', '),
    maxWidth: '94%',
    wordBreak: 'keep-all' as const,
  }

  return (
    <AbsoluteFill style={{
      justifyContent: 'flex-end', alignItems: 'center',
      padding: `0 40px ${bottomPad}px`,
      boxSizing: 'border-box', pointerEvents: 'none',
    }}>
      {/* 롱폼 임팩트: 검은 배경 박스 (레퍼런스 15번 frame_000104) */}
      {!isShorts && isImpact ? (
        <div style={{
          opacity, transform: `translateY(${ty}px)`,
          backgroundColor: 'rgba(0,0,0,0.88)',
          padding: `${fontSize * 0.28}px ${fontSize * 0.65}px`,
          borderRadius: 4,
          maxWidth: '98%',
        }}>
          <span style={{
            color: '#ffffff',
            fontSize: fontSize * 1.04,
            fontWeight: 900,
            textAlign: 'center',
            display: 'block',
            lineHeight: 1.35,
            letterSpacing: '-0.01em',
            wordBreak: 'keep-all',
          }}>
            {text}
          </span>
        </div>
      ) : (
        <div style={outlineStyle}>{text}</div>
      )}
    </AbsoluteFill>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 메인 컴포지션
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export const VideoComposition: React.FC<RemotionInput> = (input) => {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()

  // 포맷 판별 — 세로가 가로보다 길면 숏폼
  const isShorts = height > width
  const isLongform = !isShorts

  const { scene, localFrame, sceneDuration } = useMemo(
    () => getSceneInfo(frame, input.scenes ?? [], fps),
    [frame, fps, input.scenes]
  )

  const srtText = useMemo(
    () => getSrt(frame / fps, input.subtitles ?? []),
    [frame, fps, input.subtitles]
  )

  if (!scene) return <AbsoluteFill style={{ backgroundColor: '#000' }} />

  const role = scene.role as Role

  // ── 롱폼 전용 조건 ──────────────────────────────────
  // StatBox: 롱폼에서만, stat/hook + 수치 있을 때
  const showStatBox = isLongform && (role === 'stat' || role === 'hook') && hasNum(scene.subtitle)

  // 임팩트 자막: 롱폼에서만
  //   stat 씬 중 수치가 없는 경우 (이미지에 수치가 있고 자막은 설명문)
  //   problem 씬 중 짧은 강조 문장 (18자 이하)
  const isImpactSubtitle = isLongform && (
    (role === 'stat' && !hasNum(scene.subtitle)) ||
    (role === 'problem' && (srtText?.length ?? 99) <= 18)
  )

  // 좌상단 레이블: 롱폼에서만 (numbered/problem/stat)
  const showContextLabel = isLongform && (role === 'numbered' || role === 'problem' || role === 'stat')

  // 플로팅 키워드: 롱폼에서만 (hook/problem/solution)
  const showFloating = isLongform && (role === 'hook' || role === 'problem' || role === 'solution')

  // CTA: 롱폼에서만 closing 씬
  const showCta = isLongform && role === 'closing'

  // 숏폼 상단 배너: 숏폼에서만, closing 씬 제외
  const showShortsBanner = isShorts && role !== 'closing'

  // ── 해상도별 자막 수치 ───────────────────────────────
  // 숏폼: 더 큰 글씨, 더 아래 위치 (레퍼런스 398 스타일)
  // 롱폼: 표준
  const srtFontSize = isShorts ? 48 : isLongform ? 30 : 44
  const srtBottom   = isShorts ? 80 : isLongform ? 48 : 60

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {input.fullAudioFile && <Audio src={staticFile(input.fullAudioFile)} />}

      {/* ① 배경 Ken Burns */}
      <KenBurns
        bgImage={scene.bgImage} bgColor={scene.bgColor}
        localFrame={localFrame} sceneDuration={sceneDuration} role={role}
      />

      {/* ② 그라디언트 오버레이 */}
      <Gradient role={role} isShorts={isShorts} localFrame={localFrame} fps={fps} />

      {/* ③ [숏폼] 상단 고정 제목 배너 */}
      {showShortsBanner && (
        <ShortsTitleBanner
          title={input.title}
          localFrame={localFrame} fps={fps} width={width}
        />
      )}

      {/* ④ [롱폼] 플로팅 감정 키워드 (hook/problem/solution) */}
      {showFloating && (
        <FloatingWords
          role={role}
          localFrame={localFrame} fps={fps}
          sceneDuration={sceneDuration} isLongform={isLongform}
        />
      )}

      {/* ⑤ [롱폼] 좌상단 맥락 레이블 (numbered/problem/stat) */}
      {showContextLabel && (
        <ContextLabel
          role={role} subtitle={scene.subtitle} index={scene.index}
          localFrame={localFrame} fps={fps} isLongform={isLongform}
        />
      )}

      {/* ⑥ [롱폼] 수치 강조 StatBox (stat/hook + 숫자) */}
      {showStatBox && (
        <StatBox
          text={scene.subtitle} role={role}
          localFrame={localFrame} fps={fps}
          sceneDuration={sceneDuration} isLongform={isLongform}
        />
      )}

      {/* ⑦ [롱폼] CTA 원형 버튼 (closing) */}
      {showCta && (
        <CtaOverlay
          localFrame={localFrame} fps={fps} isLongform={isLongform}
        />
      )}

      {/* ⑧ SRT 자막 (항상 — 포맷·role에 따라 스타일 분기) */}
      {srtText && (
        <SrtLine
          text={srtText} role={role}
          isImpact={isImpactSubtitle} isShorts={isShorts}
          localFrame={localFrame} fps={fps}
          bottomPad={srtBottom} fontSize={srtFontSize}
        />
      )}

      {/* ⑨ 씬 전환 와이프 엣지 */}
      <WipeEdge localFrame={localFrame} fps={fps} />
    </AbsoluteFill>
  )
}
