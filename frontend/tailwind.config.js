/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        black: {
          0:   '#FFFFFF',
          100: '#E8E8E8',
          200: '#CDCECF',
          300: '#9B9C9E',
          400: '#686B6E',
          500: '#363A3D',
          600: '#1A1D21',
          700: '#131619',
          800: '#0D0F10',
          900: '#060708',
        },
        purple: {
          200: '#DECCFB',
          300: '#BD9AF8',
          400: '#9C67F4',
          500: '#7C35F1',
          600: '#5F18D4',
          700: '#47129F',
        },
        blue: {
          100: '#EBEDFC',
          200: '#D2D8F9',
          300: '#A6B0F2',
          400: '#7989EC',
          500: '#4D62E5',
          600: '#3045C9',
          700: '#243497',
          800: '#1A2342',
        },
        green: {
          600: '#4AC97E',
        },
        red: {
          500: '#FF5F57',
          600: '#F03A38',
          900: '#431B1C',
        },
        yellow: {
          400: '#FFD147',
          500: '#E2B42B',
        },
        lime: {
          800: '#3f6212',
        },
        gold: {
          300: '#f0d080',
          400: '#c89b3c',
          500: '#a47d2e',
        },
        accent: {
          red:   '#F03A38',
          green: '#4AC97E',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'hxl': ['32px', { lineHeight: '1.1', fontWeight: '600' }],
        'hxs': ['20px', { lineHeight: '1.2', fontWeight: '600' }],
        'bxl': ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        'bm':  ['14px', { lineHeight: '1.4', fontWeight: '500' }],
        'bs':  ['12px', { lineHeight: '1.5', fontWeight: '500' }],
        'bxs': ['10px', { lineHeight: '1.5', fontWeight: '500' }],
      },
      animation: {
        'fade-up':    'fadeUp 0.4s ease forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'pulse-dot':  'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
      },
    },
  },
  plugins: [],
}
