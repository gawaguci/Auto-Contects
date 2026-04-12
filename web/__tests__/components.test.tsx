import { render, screen } from '@testing-library/react'
import { Text, Heading, Label } from '../app/design-system/components/typography'
import { Box, Stack, Container, Grid } from '../app/design-system/components/layout'

describe('Text component', () => {
  it('renders as <p> by default', () => {
    render(<Text>Hello</Text>)
    expect(screen.getByText('Hello').tagName).toBe('P')
  })

  it('renders as custom element via `as` prop', () => {
    render(<Text as="span">Hello</Text>)
    expect(screen.getByText('Hello').tagName).toBe('SPAN')
  })

  it('applies size class', () => {
    render(<Text size="sm">Small</Text>)
    expect(screen.getByText('Small')).toHaveClass('text-sm')
  })

  it('applies truncate class', () => {
    render(<Text truncate>Truncated</Text>)
    expect(screen.getByText('Truncated')).toHaveClass('truncate')
  })
})

describe('Heading component', () => {
  it('renders as <h2> by default', () => {
    render(<Heading>Title</Heading>)
    expect(screen.getByText('Title').tagName).toBe('H2')
  })

  it('renders the correct heading level', () => {
    render(<Heading level={1}>Main</Heading>)
    expect(screen.getByText('Main').tagName).toBe('H1')
  })

  it('accepts custom size override', () => {
    render(<Heading level={3} size="4xl">Big H3</Heading>)
    expect(screen.getByText('Big H3')).toHaveClass('text-4xl')
  })
})

describe('Label component', () => {
  it('renders a <label> element', () => {
    render(<Label>Name</Label>)
    expect(screen.getByText('Name').tagName).toBe('LABEL')
  })

  it('shows required asterisk when required=true', () => {
    render(<Label required>Email</Label>)
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('applies disabled styles', () => {
    render(<Label disabled>Disabled</Label>)
    expect(screen.getByText('Disabled')).toHaveClass('cursor-not-allowed')
  })
})

describe('Box component', () => {
  it('renders as <div> by default', () => {
    render(<Box>content</Box>)
    expect(screen.getByText('content').tagName).toBe('DIV')
  })

  it('applies padding class', () => {
    render(<Box padding="4">content</Box>)
    expect(screen.getByText('content')).toHaveClass('p-4')
  })

  it('applies border class', () => {
    render(<Box border>content</Box>)
    expect(screen.getByText('content')).toHaveClass('border')
  })
})

describe('Stack component', () => {
  it('renders flex-col by default', () => {
    render(<Stack>item</Stack>)
    expect(screen.getByText('item')).toHaveClass('flex-col')
  })

  it('renders flex-row when direction=row', () => {
    render(<Stack direction="row">item</Stack>)
    expect(screen.getByText('item')).toHaveClass('flex-row')
  })

  it('applies gap class', () => {
    render(<Stack gap="6">item</Stack>)
    expect(screen.getByText('item')).toHaveClass('gap-6')
  })
})

describe('Container component', () => {
  it('renders with max-width class', () => {
    render(<Container>content</Container>)
    expect(screen.getByText('content')).toHaveClass('max-w-[1280px]')
  })

  it('applies custom size', () => {
    render(<Container size="md">content</Container>)
    expect(screen.getByText('content')).toHaveClass('max-w-[768px]')
  })

  it('centers by default', () => {
    render(<Container>content</Container>)
    expect(screen.getByText('content')).toHaveClass('mx-auto')
  })
})

describe('Grid component', () => {
  it('renders grid with 1 col by default', () => {
    render(<Grid>item</Grid>)
    expect(screen.getByText('item')).toHaveClass('grid-cols-1')
  })

  it('applies cols prop', () => {
    render(<Grid cols={3}>item</Grid>)
    expect(screen.getByText('item')).toHaveClass('grid-cols-3')
  })
})
