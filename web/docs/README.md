# Auto Content Design System

OKLCH 기반 디자인 시스템. 유튜브 영상 자동 생성 파이프라인 웹 UI를 위한 Foundation 스코프 컴포넌트 라이브러리.

## Quick Start

```tsx
// 1. CSS import (globals.css에 이미 포함)
import './design-system/themes/tokens.css'

// 2. 컴포넌트 사용
import { Text, Heading, Label } from './design-system'
import { Box, Stack, Container, Grid } from './design-system'

export default function Page() {
  return (
    <Container>
      <Stack gap="6">
        <Heading level={1}>Auto Content</Heading>
        <Text size="lg" color="secondary">영상 자동 생성 대시보드</Text>
      </Stack>
    </Container>
  )
}
```

## 토큰 시스템

디자인 시스템은 3단계 토큰 계층을 사용합니다:

```
Primitive  →  Semantic  →  Component
--color-primary-600  →  --interactive-primary  →  (컴포넌트 내부)
```

**컴포넌트는 절대 프리미티브 토큰을 직접 사용하지 않습니다.**

## 빠른 토큰 참조

| 용도 | 토큰 |
|------|------|
| 페이지 배경 | `var(--surface-default)` |
| 카드 배경 | `var(--surface-raised)` |
| 본문 텍스트 | `var(--text-primary)` |
| 보조 텍스트 | `var(--text-secondary)` |
| 기본 액션 | `var(--interactive-primary)` |
| 오류 상태 | `var(--state-error)` |
| 포커스 링 | `var(--border-focus)` |
| 기본 테두리 | `var(--border-default)` |

## 스크립트

```bash
npm run test           # 테스트 실행
npm run test:watch     # 워치 모드
npm run typecheck      # 타입 체크
npm run tokens:build   # Style Dictionary 토큰 빌드 (CSS + JS + Android XML)
npm run test:ci        # CI 전체 (typecheck + test + tokens:build)
```

## 파일 구조

```
app/design-system/
├── components/
│   ├── layout/       # Box, Stack, Container, Grid
│   └── typography/   # Text, Heading, Label
├── themes/
│   └── tokens.css    # 메인 토큰 CSS (Tailwind v4 @theme + semantic)
├── tokens/
│   ├── primitive/    # OKLCH 원시 컬러 값 (TS)
│   ├── dtcg/         # Style Dictionary 입력 (JSON)
│   └── dist/         # 빌드 출력 (CSS, JS, Android XML)
├── utils/
│   ├── cn.ts         # clsx + tailwind-merge
│   ├── oklch.ts      # OKLCH 변환 유틸리티
│   └── contrast.ts   # APCA 대비 계산
└── index.ts          # Public API
```
