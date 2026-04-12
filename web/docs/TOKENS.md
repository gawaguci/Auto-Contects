# Token Guide — Auto Content Design System

## 토큰 계층

### 1. Primitive Tokens (프리미티브)

`@theme` 블록에 정의. Tailwind 유틸리티 클래스 생성.

```css
--color-primary-500: oklch(0.60 0.10 250);  /* → bg-primary-500, text-primary-500 */
--color-neutral-50:  oklch(0.98 0.005 250); /* → bg-neutral-50 */
--spacing-4: 16px;                           /* → p-4, m-4, gap-4 */
--radius-default: 8px;                       /* → rounded-default */
```

**컴포넌트에서 직접 사용 금지.** Tailwind 유틸리티 또는 시맨틱 토큰으로만 접근.

### 2. Semantic Tokens (시맨틱)

`@layer tokens :root` 에 정의. 의미 기반 명칭.

```css
--surface-default:    var(--color-neutral-50);
--text-primary:       var(--color-neutral-900);
--interactive-primary: var(--color-primary-600);
--state-error:        var(--color-error);
```

**컴포넌트에서 이 토큰만 소비합니다.**

### 3. Component Tokens (컴포넌트)

향후 버튼, 인풋 등 인터랙티브 컴포넌트 추가 시 정의.

## 시맨틱 토큰 전체 목록

### Surface
| 토큰 | 값 | 용도 |
|------|----|------|
| `--surface-default` | L=0.98 | 메인 배경 |
| `--surface-raised` | white | 카드, 모달 |
| `--surface-overlay` | L=0.94 | 사이드바, 섹션 배경 |
| `--surface-muted` | L=0.94 | 스켈레톤, 비활성 |
| `--surface-inverse` | L=0.18 | 다크 강조 |

### Text
| 토큰 | 값 | 용도 |
|------|----|------|
| `--text-primary` | L=0.18 | 본문, 제목 |
| `--text-secondary` | L=0.52 | 캡션, 메타데이터 |
| `--text-tertiary` | L=0.65 | 플레이스홀더 |
| `--text-disabled` | L=0.78 | 비활성 |
| `--text-inverse` | white | 다크 배경 위 |
| `--text-brand` | primary-600 | 링크, 브랜드 |

### Border
| 토큰 | 용도 |
|------|------|
| `--border-subtle` | 낮은 강조 구분 |
| `--border-default` | 표준 테두리 |
| `--border-strong` | 고강조 |
| `--border-focus` | 키보드 포커스 |

### Interactive
| 토큰 | 용도 |
|------|------|
| `--interactive-primary` | CTA 배경 |
| `--interactive-primary-hover` | 호버 |
| `--interactive-primary-active` | 눌림 |
| `--interactive-primary-bg` | 틴트 배경 |
| `--interactive-primary-text` | 브랜드 텍스트 |

### State
| 토큰 | 용도 |
|------|------|
| `--state-success` / `--state-success-bg` | 성공 |
| `--state-warning` / `--state-warning-bg` | 경고 |
| `--state-error` / `--state-error-bg` | 오류 |
| `--state-info` / `--state-info-bg` | 정보 |

## 새 토큰 추가 방법

1. `app/design-system/themes/tokens.css`의 `@theme`에 프리미티브 추가
2. `@layer tokens :root`에 시맨틱 토큰 추가 (`var()` 참조)
3. `app/design-system/tokens/primitive/` TypeScript 파일 업데이트
4. DTCG JSON(`tokens/dtcg/`) 업데이트 후 `npm run tokens:build`
5. DESIGN.md에 결정 사항 기록

## Multi-platform 출력

`npm run tokens:build` 실행 시:

- `tokens/dist/tokens.js` — JavaScript/TypeScript 소비
- `themes/generated/primitives.css` — CSS 오버라이드
- `tokens/dist/android/colors.xml` — Android XML
