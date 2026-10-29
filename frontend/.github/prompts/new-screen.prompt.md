---
description: "Cria uma tela/página nova com loading, error handling, data fetching e layout responsivo seguindo os padrões do mvp.gg"
agent: "frontend-dev"
argument-hint: "Nome e descrição da tela (ex: 'SettingsScreen com opções de configuração')"
---
Crie uma nova tela (screen) para o projeto mvp.gg.

## Requisitos
1. Leia as telas existentes em `src/screens/` para seguir o mesmo padrão
2. Leia `.github/instructions/screens.instructions.md` para entender o padrão tri-state
3. Crie a tela em `src/screens/[Nome]Screen.jsx`
4. Inclua: useState (data, loading, error), useEffect para fetch, useNavigate
5. Loading state com shimmer-bg skeleton
6. Error state com mensagem amigável em português
7. Background: `bg-black-700`, Container: `max-w-[1200px] mx-auto px-4`
8. Animações de entrada: `animate-fade-up` com delays incrementais
9. Responsivo: mobile-first, `lg:` para desktop
10. Adicione a rota no `src/App.jsx`
