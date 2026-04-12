import React, { useMemo } from 'react'
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion'

type Scene = {
  index: number
  duration: number
  narration: string
  subtitle: string
  imagePrompt: string
  bgColor: string
  bgImage: string
  audioFile: string
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

const toFrames = (seconds: number, fps: number): number => Math.max(1, Math.ceil(seconds * fps))

const sceneOffsets = (scenes: Scene[], fps: number): Array<{ start: number; end: number }> => {
  let cursor = 0
  return scenes.map((scene) => {
    const duration = toFrames(scene.duration, fps)
    const start = cursor
    const end = start + duration
    cursor = end
    return { start, end }
  })
}

const currentSceneAtFrame = (frame: number, scenes: Scene[], fps: number): Scene | null => {
  const offsets = sceneOffsets(scenes, fps)
  for (let i = 0; i < offsets.length; i += 1) {
    const range = offsets[i]
    if (frame >= range.start && frame < range.end) {
      return scenes[i]
    }
  }
  return scenes.length > 0 ? scenes[scenes.length - 1] : null
}

const currentSubtitleAtSecond = (seconds: number, subtitles: SubtitleItem[]): string | null => {
  const found = subtitles.find((s) => seconds >= s.start && seconds <= s.end)
  return found?.text ?? null
}

export const VideoComposition: React.FC<RemotionInput> = (input) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const scene = useMemo(() => currentSceneAtFrame(frame, input.scenes ?? [], fps), [frame, fps, input.scenes])
  const subtitle = useMemo(
    () => currentSubtitleAtSecond(frame / fps, input.subtitles ?? []),
    [frame, fps, input.subtitles]
  )

  const hasBgImage = Boolean(scene?.bgImage && scene.bgImage.trim().length > 0)
  const bgColor = scene?.bgColor || '#101018'

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {input.fullAudioFile ? <Audio src={staticFile(input.fullAudioFile)} /> : null}

      <AbsoluteFill style={{ backgroundColor: bgColor }}>
        {hasBgImage ? (
          <Img
            src={staticFile(scene!.bgImage)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        ) : null}
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.35) 40%, rgba(0,0,0,0.08) 100%)',
        }}
      />

      {subtitle ? (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'center',
            padding: '0 72px 160px',
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              color: '#fff',
              fontSize: 58,
              fontWeight: 800,
              textAlign: 'center',
              lineHeight: 1.15,
              textShadow: '0 4px 14px rgba(0,0,0,0.8)',
              letterSpacing: '-0.02em',
            }}
          >
            {subtitle}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  )
}
