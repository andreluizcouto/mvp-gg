---
description: "Use when creating or editing React components in src/components/. Covers component structure, hooks usage, props patterns, and reusability guidelines for the mvp.gg project."
applyTo: "src/components/**"
---
# Padrões de Componentes React — mvp.gg

## Estrutura de Componente
```jsx
import { useState, useEffect } from 'react';

export default function NomeDoComponente({ prop1, prop2 }) {
  // 1. Hooks primeiro (useState, useEffect, useNavigate, etc.)
  // 2. Handlers / funções auxiliares
  // 3. Early returns (loading, error)
  // 4. Return JSX principal

  return (
    <div className="...">
      {/* JSX */}
    </div>
  );
}
```

## Regras
- Um componente por arquivo, PascalCase no nome
- Props SEMPRE desestruturadas no parâmetro: `({ prop1, prop2 })`
- Nunca usar `class`, sempre `className`
- Nunca usar inline styles (`style={}`), sempre Tailwind via className
- Usar `export default function` (não arrow function exportada)
- Componentes filhos menores podem ser definidos no mesmo arquivo se forem usados APENAS ali
- Imagens de champions via DDV: `https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${championName}.png`

## Hooks
- `useState` para estado local
- `useEffect` para side effects (fetch, timers) — sempre com cleanup
- `useNavigate()` para navegação programática
- `useParams()` para extrair parâmetros de rota
- `useLocation()` para acessar state passado na navegação

## Condicionais no JSX
```jsx
{/* Ternário para if/else */}
{isLoading ? <Skeleton /> : <Content />}

{/* && para if simples */}
{hasError && <ErrorMessage />}

{/* Nunca usar if/else inline — extrair para variável ou early return */}
```

## Listas
```jsx
{items.map((item, index) => (
  <ItemComponent key={item.id || index} item={item} />
))}
```
- Sempre usar `key` única (preferir ID sobre index)
