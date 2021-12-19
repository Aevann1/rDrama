const colors = require('tailwindcss/colors')

module.exports = {
  mode: 'jit',
  purge: [
  'files/templates/**/*.html',
  'files/templates/*.html'
  ],
  darkMode: 'class', // or 'media' or 'class'
  theme: {
    colors: {
      primary: ({ opacityVariable, opacityValue }) => {
        if (opacityValue !== undefined) {
          return `rgba(var(--color-primary), ${opacityValue})`
        }
        if (opacityVariable !== undefined) {
          return `rgba(var(--color-primary), var(${opacityVariable}, 1))`
        }
        return `rgb(var(--color-primary))`
      },
      transparent: 'transparent',
      current: 'currentColor',
      black: colors.black,
      white: colors.white,
      pink: colors.pink,
      purple: colors.purple,
      green: colors.green,
      red: colors.red,
      yellow: colors.amber,
      blue: colors.sky
    },
    fontFamily: {
      'sans-serif': ['Helvetica Neue', '-apple-system', 'BlinkMacSystemFont', 'Tahoma', 'Segoe UI', 'Helvetica', 'sans-serif', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'],
      'heading': ['Delius Swash Caps'],
      'serif': ['Georgia'],
      'mono': 'SFMono-Regular,Consolas,Liberation Mono,Menlo,Courier,monospace'
    },
    extend: {
      boxShadow: {
        'inset-b-white-07': '-1px -1px 1px rgba(255, 255, 255, 0.07) inset',
        'inset-t-white-05': '0 1px 0 rgba(255, 255, 255, 0.05) inset',
        'inset-t-white-10': '0 1px 0 rgba(255, 255, 255, 0.10) inset',
        'inset-r-white-05': '1px 0 0 rgba(255, 255, 255, 0.05) inset'
      },
      zIndex: {
        '100': 100
      },
      colors: {
        gray: {
          100: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-100), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-100), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-100))`;
          },
          200: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-200), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-200), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-200))`;
          },
          300: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-300), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-300), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-300))`;
          },
          400: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-400), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-400), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-400))`;
          },
          500: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-500), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-500), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-500))`;
          },
          600: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-600), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-600), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-600))`;
          },
          700: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-700), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-700), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-700))`;
          },
          800: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-800), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-800), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-800))`;
          },
          900: ({ opacityVariable, opacityValue }) => {
            if (opacityValue !== undefined) {
              return `rgba(var(--color-900), ${opacityValue})`;
            }
            if (opacityVariable !== undefined) {
              return `rgba(var(--color-900), var(${opacityVariable}, 1))`;
            }
            return `rgb(var(--color-900))`;
          },
        }
      }
    },
  },
  variants: {
    extend: {
      backgroundColor: ['checked'],
      boxShadow: ['checked'],
      color: ['checked']
    },
  },
  plugins: [],
}
