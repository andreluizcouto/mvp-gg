/** @type {import('tailwindcss').Config} */
// Identidade mvp.gg: o mapa visto de cima.
// Tinta azul-noite de fundo, ouro do selo de MVP como destaque e um ciano "hextech" para dados.
// Os nomes das escalas (black/blue/purple) foram mantidos para não reescrever as telas antigas:
// black = tinta, blue = ciano de dados, purple/gold = ouro do MVP.
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
          100: '#E8ECF3',
          200: '#C5CCD9',
          300: '#97A0B3',
          400: '#6E778A',
          500: '#262E3D',
          600: '#161C27',
          700: '#0D121A',
          800: '#090D13',
          900: '#05070B',
        },
        blue: {
          100: '#DDFBF7',
          200: '#AEF2EA',
          300: '#73E4D8',
          400: '#33D1C1',
          500: '#16B2A4',
          600: '#0E8D82',
          700: '#0B6C64',
          800: '#0B2A2B',
        },
        purple: {
          200: '#F6E7BF',
          300: '#EED394',
          400: '#E2B95E',
          500: '#C99A36',
          600: '#A57A22',
          700: '#7A5916',
        },
        gold: {
          300: '#F6E2A6',
          400: '#E2B95E',
          500: '#C99A36',
        },
        green: {
          400: '#5BE6A8',
          600: '#3DD68C',
        },
        red: {
          400: '#FF7B8A',
          500: '#FF5A6E',
          600: '#F0445A',
          900: '#3A1820',
        },
        yellow: {
          400: '#FFD166',
          500: '#E8B53A',
        },
        lime: {
          800: '#3f6212',
        },
        accent: {
          red:   '#FF5A6E',
          green: '#3DD68C',
        },
      },
      fontFamily: {
        sans:    ['"Inter Variable"', 'system-ui', 'sans-serif'],
        display: ['"Unbounded Variable"', '"Inter Variable"', 'system-ui', 'sans-serif'],
      },
      // Nenhum texto abaixo de 12px (guia de sites, parte 2).
      fontSize: {
        'hxl': ['32px', { lineHeight: '1.1', fontWeight: '600' }],
        'hxs': ['20px', { lineHeight: '1.25', fontWeight: '600' }],
        'bxl': ['18px', { lineHeight: '1.35', fontWeight: '600' }],
        'bm':  ['15px', { lineHeight: '1.5', fontWeight: '500' }],
        'bs':  ['13px', { lineHeight: '1.5', fontWeight: '500' }],
        'bxs': ['12px', { lineHeight: '1.5', fontWeight: '500' }],
      },
      borderRadius: {
        card: '18px',
      },
      boxShadow: {
        card: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 12px 32px -12px rgba(0,0,0,0.6)',
        glow: '0 0 0 1px rgba(226,185,94,0.35), 0 10px 40px -10px rgba(226,185,94,0.35)',
      },
      animation: {
        'fade-up':    'fadeUp 0.5s cubic-bezier(.2,.7,.2,1) forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'pulse-dot':  'pulseDot 2s ease-in-out infinite',
        // "both": durante o atraso a linha fica apagada, sem piscar desenhada antes de começar
        'lane-draw':  'laneDraw 2.4s cubic-bezier(.6,0,.2,1) both',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(14px)' },
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
        laneDraw: {
          '0%':   { strokeDashoffset: '1' },
          '100%': { strokeDashoffset: '0' },
        },
      },
    },
  },
  plugins: [],
}
