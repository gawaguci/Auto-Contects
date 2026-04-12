// Style Dictionary 4.x — Multi-platform token output
// Generates CSS (web), JS constants (React Native), and Android XML

import StyleDictionary from 'style-dictionary'

const sd = new StyleDictionary({
  source: ['app/design-system/tokens/dtcg/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'app/design-system/themes/generated/',
      files: [
        {
          destination: 'primitives.css',
          format: 'css/variables',
          options: { outputReferences: false },
        },
      ],
    },
    js: {
      transformGroup: 'js',
      buildPath: 'app/design-system/tokens/dist/',
      files: [
        {
          destination: 'tokens.js',
          format: 'javascript/esm',
        },
      ],
    },
    android: {
      transformGroup: 'android',
      buildPath: 'app/design-system/tokens/dist/android/',
      files: [
        {
          destination: 'colors.xml',
          format: 'android/colors',
          filter: (token) => token.$type === 'color',
        },
      ],
    },
  },
})

await sd.buildAllPlatforms()
console.log('✓ Style Dictionary: multi-platform tokens generated')
