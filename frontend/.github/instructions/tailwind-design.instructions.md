---
description: "Use when working with Tailwind CSS, styling, layout, colors, typography, animations, or responsive design in the mvp.gg project. Complete design system reference."
applyTo: "src/**/*.{jsx,css}"
---
# Design System Tailwind — mvp.gg (baseado no dpm.lol)

## Cores Customizadas (tailwind.config.js)

### Backgrounds (escuro → claro)
| Token | Hex | Uso |
|-------|-----|-----|
| `black-900` | #060708 | Background mais escuro (footer) |
| `black-800` | #0D0F10 | Navbar, cards principais |
| `black-700` | #131619 | **Background padrão da página** |
| `black-600` | #1A1D21 | Cards secundários, hover states |
| `black-500` | #363A3D | Bordas, divisores |

### Texto
| Token | Hex | Uso |
|-------|-----|-----|
| `black-0` | #FFFFFF | Títulos, texto principal |
| `black-100` | #E8E8E8 | Texto destaque |
| `black-200` | #CDCECF | Texto corpo |
| `black-300` | #9B9C9E | Texto secundário, labels |
| `black-400` | #686B6E | Texto muted, placeholders |

### Accent
| Token | Hex | Uso |
|-------|-----|-----|
| `blue-400` | #7989EC | **Accent principal** — barras, hover, badges, links |
| `blue-500` | #4D62E5 | Botões CTA |
| `blue-600` | #3045C9 | Hover de botões |

### Semânticas
| Token | Hex | Uso |
|-------|-----|-----|
| `green-600` | #4AC97E | Vitória, positivo |
| `red-600` | #F03A38 | Derrota, negativo |
| `yellow-400` | #FFD147 | Neutro (win rate 50-60%) |
| `gold-400` | #c89b3c | Coaching IA accent |

### Premium
| Token | Hex | Uso |
|-------|-----|-----|
| `purple-200` | #DECCFB | Texto premium (coaching unlock) |
| `purple-500` | #7C35F1 | Badges premium, botões secundários |

## Tipografia
- Fonte: **Plus Jakarta Sans** (weight 400-800)
- Tamanhos customizados:
  - `text-hxl` = 32px/600 (hero titles)
  - `text-hxs` = 20px/600 (summoner name desktop)
  - `text-bxl` = 18px/600 (summoner name)
  - `text-bm` = 14px/500 (nav, labels)
  - `text-bs` = 12px/500 (stats, body)
  - `text-bxs` = 10px/500 (small labels)

## Cards
```jsx
<div className="bg-black-800 rounded-xl p-4 shadow-[0_2px_8px_rgba(121,137,236,0.10)]">
  {/* Card content */}
</div>
```
- Background: `bg-black-800`
- Border radius: `rounded-xl` (12px)
- Shadow: `shadow-[0_2px_8px_rgba(121,137,236,0.10)]` (glow azul sutil)
- Padding: `p-4` ou `p-6`

## Botões
```jsx
{/* CTA Principal */}
<button className="bg-blue-500 hover:bg-blue-600 text-black-0 font-semibold px-6 py-2 rounded-lg transition-colors">
  Texto
</button>

{/* Botão Secundário */}
<button className="bg-black-600 hover:bg-black-500 text-black-200 px-4 py-2 rounded-lg transition-colors">
  Texto
</button>
```

## Animações CSS (index.css)
| Classe | Efeito |
|--------|--------|
| `animate-fade-up` | Fade in + slide up (entrada) |
| `animate-fade-in` | Fade in simples |
| `shimmer-bg` | Loading skeleton shimmer |
| `glow-purple` | Brilho roxo (perfil header) |
| `scoreGlow` | Pulso azul (score badges) |
| `text-premium` | Gradiente roxo no texto |

## Responsividade
- **Mobile-first**: Estilos base = mobile
- **Desktop**: Prefixo `lg:` (≥1024px)
- Nunca usar `sm:` ou `md:` sozinhos — manter consistência mobile → lg

## Regras de Ouro
1. NUNCA usar cores hardcoded (#hex) — sempre tokens do Tailwind config
2. NUNCA usar CSS modules ou styled-components
3. NUNCA usar `style={}` inline — sempre className
4. Hover sempre com `transition-colors` ou `transition-all`
5. Espaçamento vertical entre seções: `space-y-4` ou `gap-4`
6. Container padrão: `max-w-[1200px] mx-auto px-4`
