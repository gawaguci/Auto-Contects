# Contributing Guide — Auto Content Design System

## 새 컴포넌트 추가

### 1. 디렉토리 구조

```
app/design-system/components/
└── {category}/
    ├── {ComponentName}.tsx
    └── index.ts          # barrel export
```

카테고리: `typography`, `layout`, `interactive` (향후), `feedback` (향후)

### 2. 컴포넌트 템플릿

```tsx
import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

interface MyComponentProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
}

export const MyComponent = forwardRef<HTMLDivElement, MyComponentProps>(
  function MyComponent({ variant = 'default', size = 'md', className, children, ...props }, ref) {
    return (
      <div
        ref={ref}
        className={cn(
          /* 시맨틱 토큰만 사용 */
          '[background:var(--surface-raised)]',
          '[color:var(--text-primary)]',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

MyComponent.displayName = 'MyComponent'
```

### 3. 필수 규칙

- **시맨틱 토큰만** — `--text-primary` ✓, `--color-neutral-900` ✗
- **`forwardRef`** — 모든 DOM 렌더링 컴포넌트
- **`displayName`** — forwardRef 컴포넌트에 필수
- **`any` 금지** — 명시적 타입 인터페이스 사용
- **`React.FC` 금지** — named imports 사용: `import { forwardRef } from 'react'`
- **lint 억제 금지** — `@ts-ignore`, `eslint-disable` 없음
- **하드코딩 색상 금지** — hex, rgb(), hsl() 직접 사용 없음
- **인터랙티브 테두리** — CSS border 대신 `box-shadow: 0 0 0 1px var(--border-default)`

### 4. 인터랙티브 상태 구현 가이드

버튼, 인풋 등 인터랙티브 컴포넌트:

```tsx
// hover/focus/active는 CSS :pseudo 사용 — JS 상태 관리 금지
className={cn(
  '[background:var(--interactive-primary)]',
  '[color:var(--text-inverse)]',
  'hover:[background:var(--interactive-primary-hover)]',
  'active:[background:var(--interactive-primary-active)]',
  'disabled:opacity-40 disabled:cursor-not-allowed',
  // 포커스 링은 globals.css의 :focus-visible로 전역 처리됨
)}
```

### 5. 배럴 export 업데이트

```ts
// components/{category}/index.ts
export { MyComponent } from './MyComponent'

// app/design-system/index.ts
export { MyComponent } from './components/{category}'
```

### 6. 테스트 작성

```tsx
// __tests__/components.test.tsx에 describe 블록 추가

describe('MyComponent', () => {
  it('renders with default props', () => {
    render(<MyComponent>content</MyComponent>)
    expect(screen.getByText('content').tagName).toBe('DIV')
  })

  it('applies variant class', () => {
    render(<MyComponent variant="secondary">content</MyComponent>)
    // 구현한 클래스 검증
  })
})
```

### 7. APCA 대비 검증

새 텍스트/배경 쌍 추가 시:

```ts
import { apcaContrast, meetsContrastThreshold } from '../app/design-system/utils/contrast'

// 검증
const lc = apcaContrast(fgLightness, bgLightness)
console.assert(Math.abs(lc) >= 60, `APCA contrast ${lc} below Lc 60 threshold`)
```

### 8. CI 체크

```bash
npm run test:ci  # typecheck + test + tokens:build
```

모두 통과해야 PR 가능.

## 토큰 변경 시

1. `tokens.css` 수정 (프리미티브 또는 시맨틱)
2. `tokens/primitive/` TypeScript 동기화
3. `tokens/dtcg/` JSON 업데이트 → `npm run tokens:build`
4. `DESIGN.md` 결정 로그 추가
5. 영향받는 컴포넌트 테스트 확인

## 사이즈 명명 규칙

컴포넌트 크기 변형은 항상: `x-small | small | medium | large`

Tailwind 약어(`xs`, `sm`, `md`, `lg`)는 내부 구현 매핑용으로만 사용.
