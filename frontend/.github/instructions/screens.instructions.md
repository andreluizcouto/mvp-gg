---
description: "Use when creating or editing screen/page files in src/screens/. Covers data fetching, loading/error/data states, navigation, and page layout patterns for mvp.gg."
applyTo: "src/screens/**"
---
# Padrões de Telas (Screens) — mvp.gg

## Estrutura Padrão de Tela
Toda tela que faz fetch segue o padrão tri-state:

```jsx
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function NomeDaTela() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const result = await fetchAlgo();
        setData(result);
      } catch (err) {
        setError(err.message || 'Erro ao carregar dados');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [/* dependências */]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  return (
    <div className="min-h-screen bg-black-700">
      {/* Conteúdo principal */}
    </div>
  );
}
```

## Regras
- Background principal: `bg-black-700` (NUNCA bg-black ou bg-gray)
- Container: `max-w-[1200px] mx-auto px-4`
- Sempre tratar loading, error, e data vazio
- Dados entre telas via `navigate('/rota', { state: { dados } })`
- Receber dados via `useLocation().state`
- Se state não existe → redirect para `/` com `navigate('/')`
- Títulos com `text-black-0 font-semibold`
- Subtítulos com `text-black-300`

## Padrão de Navegação
```jsx
// Enviando dados
navigate(`/summoner/${name}/${tag}`);

// Com state adicional
navigate(`/match/${matchId}`, {
  state: { matchStats, playerNick, rank, puuid }
});

// Recebendo
const location = useLocation();
const { matchStats, playerNick } = location.state || {};
if (!matchStats) { navigate('/'); return null; }
```

## Animações de Entrada
```jsx
<div className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
  {/* Staggered animation */}
</div>
```
- Use `animate-fade-up` com `animationDelay` incremental (0.1s, 0.2s, 0.3s)
- Cards e seções principais devem ter fade-in/fade-up

## Responsividade
- Layout base = mobile (1 coluna)
- Desktop via `lg:` prefix (2-4 colunas)
- Grid: `grid grid-cols-1 lg:grid-cols-4 gap-4`
- Sidebar: `lg:col-span-1`, Main: `lg:col-span-3`

## Skeleton Loading
```jsx
<div className="shimmer-bg h-4 w-32 rounded" />
```
- Use a classe `shimmer-bg` para loading placeholders
- Espelhar layout final com dimensões aproximadas
