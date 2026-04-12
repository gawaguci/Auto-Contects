# Component API Reference — Auto Content Design System

## Typography Components

### `<Text>`

일반 텍스트. 기본 `<p>` 렌더링. `as` prop으로 폴리모픽.

```tsx
import { Text } from './design-system'

<Text>본문 텍스트</Text>
<Text as="span" size="sm" color="secondary">보조 텍스트</Text>
<Text size="lg" weight="semibold" truncate>긴 텍스트 자르기...</Text>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `as` | `ElementType` | `'p'` | 렌더링 요소 |
| `size` | `'xs' \| 'sm' \| 'base' \| 'lg' \| 'xl' \| '2xl' \| '3xl' \| '4xl'` | `'base'` | 폰트 크기 |
| `weight` | `'light' \| 'normal' \| 'medium' \| 'semibold' \| 'bold'` | `'normal'` | 폰트 두께 |
| `color` | `'primary' \| 'secondary' \| 'tertiary' \| 'disabled' \| 'inverse' \| 'brand'` | `'primary'` | 텍스트 색상 |
| `truncate` | `boolean` | `false` | 텍스트 말줄임 |

---

### `<Heading>`

제목. 기본 `<h2>` 렌더링.

```tsx
import { Heading } from './design-system'

<Heading level={1}>메인 제목</Heading>
<Heading level={3} size="4xl">크기 오버라이드</Heading>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `level` | `1 \| 2 \| 3 \| 4 \| 5 \| 6` | `2` | HTML 헤딩 레벨 |
| `size` | `'base' \| 'lg' \| 'xl' \| '2xl' \| '3xl' \| '4xl'` | level별 기본값 | 크기 오버라이드 |

Level → 기본 Size 매핑: `1→4xl`, `2→3xl`, `3→2xl`, `4→xl`, `5→lg`, `6→base`

---

### `<Label>`

폼 레이블.

```tsx
import { Label } from './design-system'

<Label htmlFor="email">이메일</Label>
<Label required>필수 항목</Label>
<Label disabled>비활성 레이블</Label>
<Label size="sm">소형 레이블</Label>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `required` | `boolean` | `false` | 필수 표시 `*` 추가 (aria-hidden) |
| `disabled` | `boolean` | `false` | 비활성 스타일 |
| `size` | `'sm' \| 'base'` | `'base'` | 폰트 크기 |

---

## Layout Components

### `<Box>`

기본 레이아웃 박스. `as` prop으로 폴리모픽.

```tsx
import { Box } from './design-system'

<Box padding="4" border rounded="default" surface="raised">
  카드 콘텐츠
</Box>
<Box as="section" padding="8" surface="overlay">섹션</Box>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `as` | `ElementType` | `'div'` | 렌더링 요소 |
| `padding` | `'0'~'12'` | — | 전체 패딩 |
| `paddingX` | `'0'~'12'` | — | 수평 패딩 |
| `paddingY` | `'0'~'12'` | — | 수직 패딩 |
| `surface` | `'default' \| 'raised' \| 'overlay'` | — | 배경색 토큰 |
| `rounded` | `'none' \| 'tight' \| 'default' \| 'loose' \| 'full'` | — | 모서리 둥글기 |
| `shadow` | `'none' \| 'sm' \| 'md' \| 'lg'` | — | 그림자 |
| `border` | `boolean` | `false` | 테두리 |

---

### `<Stack>`

Flex 방향 스택.

```tsx
import { Stack } from './design-system'

<Stack gap="4">
  <div>아이템 1</div>
  <div>아이템 2</div>
</Stack>
<Stack direction="row" gap="2" align="center">
  <Icon />
  <Text>가로 스택</Text>
</Stack>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `direction` | `'row' \| 'column'` | `'column'` | 방향 |
| `gap` | `'0'~'12'` | `'4'` | 아이템 간격 |
| `align` | `'start' \| 'center' \| 'end' \| 'stretch'` | `'stretch'` | 교차축 정렬 |
| `justify` | `'start' \| 'center' \| 'end' \| 'between' \| 'around'` | `'start'` | 주축 정렬 |
| `wrap` | `boolean` | `false` | 줄 바꿈 |

---

### `<Container>`

반응형 최대 너비 컨테이너.

```tsx
import { Container } from './design-system'

<Container>콘텐츠 (기본 xl = 1280px)</Container>
<Container size="md">중형 컨테이너 (768px)</Container>
<Container size="full" center={false}>전체 너비</Container>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl' \| 'full'` | `'xl'` | 최대 너비 |
| `center` | `boolean` | `true` | `mx-auto` 중앙 정렬 |

Size → max-width: `sm=640px`, `md=768px`, `lg=1024px`, `xl=1280px`, `full=100%`

---

### `<Grid>`

CSS Grid 레이아웃.

```tsx
import { Grid } from './design-system'

<Grid cols={3} gap="6">
  <Card />
  <Card />
  <Card />
</Grid>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `cols` | `1 \| 2 \| 3 \| 4 \| 6 \| 12` | `1` | 컬럼 수 |
| `gap` | `'0'~'8'` | `'4'` | 그리드 간격 |

---

## 접근성 (Accessibility)

- `<Label required>`: 필수 `*`은 `aria-hidden="true"` — 스크린 리더는 HTML `required` 속성으로 인식
- `<Text as="span">`: 폴리모픽 `as` prop으로 시맨틱 HTML 보장
- Focus ring: `:focus-visible`에 `2px solid var(--border-focus)` 전역 적용
- APCA 대비: 기본 텍스트/배경 쌍은 Lc 60+ 충족 (secondary text는 캡션 용도로 허용)
