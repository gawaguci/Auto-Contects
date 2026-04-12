import React from 'react'
import { Composition } from 'remotion'

import { VideoComposition, type RemotionInput } from './VideoComposition'

const defaultInput: RemotionInput = {
  version: 'shorts',
  title: 'Preview',
  category: 'Preview',
  categoryEmoji: '🎬',
  categoryId: 0,
  totalDuration: 8,
  cta: '',
  fps: 30,
  width: 1080,
  height: 1920,
  fullAudioFile: '',
  scenes: [
    {
      index: 1,
      duration: 8,
      narration: 'Preview scene',
      subtitle: '미리보기',
      imagePrompt: '',
      bgColor: '#1a1a2e',
      bgImage: '',
      audioFile: '',
    },
  ],
  subtitles: [],
}

const toFrames = (seconds: number, fps: number): number => {
  return Math.max(1, Math.ceil(seconds * fps))
}

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="VideoComposition"
      component={VideoComposition}
      durationInFrames={toFrames(defaultInput.totalDuration, defaultInput.fps)}
      fps={defaultInput.fps}
      width={defaultInput.width}
      height={defaultInput.height}
      defaultProps={defaultInput}
      calculateMetadata={({ props }) => {
        const input = props as Partial<RemotionInput>
        const fps = input.fps ?? defaultInput.fps
        const width = input.width ?? defaultInput.width
        const height = input.height ?? defaultInput.height
        const totalDuration = input.totalDuration ?? defaultInput.totalDuration

        return {
          fps,
          width,
          height,
          durationInFrames: toFrames(totalDuration, fps),
        }
      }}
    />
  )
}
