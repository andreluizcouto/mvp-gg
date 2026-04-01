# Design: Coach App Local — Empacotamento como .exe (P7)

**Data:** 2026-03-28
**Status:** Aprovado

---

## Visão Geral

Empacotar o coach local (captura de minimapa + detecção de eventos) como um executável Windows distribuível, protegido com PyArmor + PyInstaller. O app roda silencioso na bandeja do sistema, captura prints do minimapa durante a partida e envia os dados ao backend (Render) para análise de IA. O usuário vê o resultado no site mvpgg.vercel.app.

---

## Arquitetura

```
[coach_app.exe]  ←── usuário abre
       │
       ├── pystray: ícone na bandeja (4 estados)
       ├── LiveCoachSession: polling localhost:2999
       ├── minimap_capture: captura canto inferior direito
       │
       │  fim de partida
       ▼
POST /local/upload  →  [Render backend]
       │                     │
       │                     ├── Gemini/Claude: analisa imagens
       │                     ├── Supabase: salva coaching
       │                     └── deleta imagens da memória
       │
GET /local/status?riot_id=...  ←── polling a cada 10s
       │
       └── ícone vira verde → usuário vai no site
```

O .exe não contém chaves de IA. Todo processamento acontece no Render.

---

## Estados do Ícone na Bandeja

| Estado | Ícone | Significado |
|---|---|---|
| `waiting` | Cinza | Aguardando LoL iniciar |
| `recording` | Dourado | Partida em andamento — gravando |
| `uploading` | Azul | Enviando dados ao backend |
| `ready` | Verde | Análise pronta — ir no site |

**Menu de contexto (botão direito):**
- Label de status (ex: "Gravando... Aurora · MID")
- **Ver análise** → abre `https://mvpgg.vercel.app` no browser padrão
- Separador
- **⚙ Configurações**
  - ☐ Minimapa à esquerda *(toggle — padrão: desmarcado)*
  - ☐ Minimapa grande *(toggle — padrão: desmarcado)*
- Separador
- **Sair**

"Ver análise" fica desabilitado (cinza) nos estados `waiting` e `recording`. Habilitado em `uploading` e `ready`.

As configurações são persistidas em `config.json` na mesma pasta do .exe. Lidas na inicialização, salvas imediatamente ao mudar o toggle. Não exigem reiniciar o app — aplicadas na próxima captura.

---

## Fluxo Completo

1. Usuário abre `CoachApp.exe` → ícone aparece na bandeja, estado `waiting`
2. App detecta LoL via polling `GET https://127.0.0.1:2999/liveclientdata/gamestats`
3. LoL detectado → identifica riotId + campeão via Live Client API
4. Estado muda para `recording` — loop de captura inicia
5. A cada morte/kill/objetivo: captura print do minimapa, salva em pasta temp
6. Live Client API para de responder → verifica fim de partida via Riot API (match IDs)
7. Match ID novo detectado → estado muda para `uploading`
8. `POST /local/upload` com `X-App-Token`, riotId, eventos + imagens base64
9. Backend processa de forma assíncrona (já existente: Gemini/Claude → Supabase)
10. App faz polling `GET /local/status?riot_id=...` a cada 10s
11. Backend retorna `ready: true` → estado muda para `ready`, imagens deletadas do servidor
12. Usuário clica "Ver análise" → abre o site

---

## Segurança

| Proteção | Implementação |
|---|---|
| Autenticação do .exe | Header `X-App-Token: <token>` em todas as chamadas ao backend. Token embutido no .exe via PyArmor (obfuscado). Backend rejeita requests sem token válido. |
| HTTPS obrigatório | Todas as chamadas ao backend usam `https://`. Render provê TLS automaticamente. |
| SHA256 publicado | Hash do `.zip` publicado na página de download. Usuário pode verificar integridade. |
| Deleção de imagens | Backend deleta imagens da memória imediatamente após salvar análise no Supabase. Imagens nunca persistem em disco no servidor. |
| Captura limitada | `minimap_capture.py` captura apenas a região do minimapa (canto definido nas configurações). Nunca tela inteira. |
| Sem elevação de privilégio | App roda com permissões de usuário comum. Não requer admin. |

---

## Configurações do Usuário

Arquivo `config.json` na mesma pasta do .exe:

```json
{
  "minimap_left": false,
  "minimap_large": false
}
```

| Chave | Padrão | Efeito |
|---|---|---|
| `minimap_left` | `false` | `true` → captura canto inferior **esquerdo** em vez do direito |
| `minimap_large` | `false` | `true` → fator de tamanho `0.27` em vez de `0.21` da altura da tela |

`minimap_capture.py` recebe `minimap_left: bool` e `minimap_large: bool` como parâmetros e calcula a região correta:

```python
# Fator de tamanho
factor = 0.27 if minimap_large else 0.21
minimap_size = int(screen_height * factor)

# Posição horizontal
left = 10 if minimap_left else screen_width - minimap_size - 10
top = screen_height - minimap_size - 10
```

---

## Novos Arquivos (ProjectB)

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `coach_app.py` | Criar | Entry point: inicializa tray + LiveCoachSession, orquestra fluxo completo |
| `tray_icon.py` | Criar | Gerencia ícone, estados, menu (com toggles de config), abertura do browser |
| `app_config.py` | Criar | Lê/salva `config.json`; expõe `get_config()` e `save_config()` |
| `assets/icon_gray.png` | Criar | Ícone estado waiting (32x32, fundo transparente) |
| `assets/icon_gold.png` | Criar | Ícone estado recording |
| `assets/icon_blue.png` | Criar | Ícone estado uploading |
| `assets/icon_green.png` | Criar | Ícone estado ready |
| `coach.spec` | Criar | Spec do PyInstaller (one-dir, inclui assets e config.json) |
| `build.bat` | Criar | Script de build: PyArmor → PyInstaller → zip |

## Arquivos Modificados (ProjectB)

| Arquivo | Modificação |
|---|---|
| `main.py` | Adicionar `POST /local/upload` e `GET /local/status` |
| `minimap_capture.py` | Aceitar `minimap_left: bool` e `minimap_large: bool` em `capture_minimap()` |
| `requirements.txt` | Adicionar `pystray>=0.19.0` |

---

## Novos Endpoints no Backend

### POST /local/upload

Recebe dados da partida do .exe. Requer header `X-App-Token`.

**Request:**
```json
{
  "riot_id": "natus vincere#navi1",
  "events": [
    {
      "event_type": "death",
      "game_time": "08:23",
      "champion": "Aurora",
      "killer": "Zed",
      "minimap_base64": "<base64 da imagem PNG>"
    }
  ]
}
```

**Response:**
```json
{ "accepted": true, "job_id": "uuid" }
```

Processamento assíncrono — não bloqueia. Backend:
1. Extrai riotId → busca match_id via Riot API
2. Chama análise de visão (Gemini/Claude) nas imagens
3. Salva resultado no Supabase (tabela `ai_cache`)
4. Deleta imagens da memória

### GET /local/status?riot_id=...

Verifica se a análise do último jogo do jogador está pronta.

**Response:**
```json
{ "ready": true, "match_id": "BR1_123456" }
```

ou

```json
{ "ready": false }
```

---

## Dependências Novas

```
pystray>=0.19.0     # system tray (runtime — vai no requirements.txt)
pyarmor>=8.0.0      # obfuscação (só build — não vai no requirements.txt)
pyinstaller>=6.0    # empacotamento (só build — não vai no requirements.txt)
```

PyArmor e PyInstaller são instalados no ambiente de build mas não incluídos no `requirements.txt` (não são dependências de runtime do servidor).

---

## Distribuição

- **Formato:** `.zip` contendo pasta `CoachApp/` com `CoachApp.exe` + DLLs
- **Tamanho estimado:** 60-90 MB comprimido
- **Download:** link direto na página do mvpgg.vercel.app
- **Verificação:** SHA256 do `.zip` publicado na mesma página

---

## O que NÃO entra nesta fase

- Instalador (.msi / NSIS) — distribuição por .zip é suficiente agora
- Auto-update automático — usuário baixa nova versão manualmente
- Suporte a múltiplos monitores — captura no monitor primário apenas
- Code signing certificate — pode ser adicionado depois se necessário
- Versão macOS/Linux — apenas Windows nesta fase
- Notificação pop-up — tray icon é suficiente

---

## Prioridades de Implementação

| # | O que | Onde |
|---|---|---|
| 1 | Ícones PNG (4 estados) | `ProjectB/assets/` |
| 2 | `app_config.py` — lê/salva config.json | `ProjectB/app_config.py` |
| 3 | Atualizar `minimap_capture.py` — aceitar `minimap_left` e `minimap_large` | `ProjectB/minimap_capture.py` |
| 4 | `tray_icon.py` — ícone, estados, menu com toggles de config | `ProjectB/tray_icon.py` |
| 5 | `coach_app.py` — entry point e orquestrador | `ProjectB/coach_app.py` |
| 6 | `POST /local/upload` + `GET /local/status` no backend | `ProjectB/main.py` |
| 7 | Teste local: rodar `coach_app.py` durante uma partida | Manual |
| 8 | `coach.spec` — configuração do PyInstaller | `ProjectB/coach.spec` |
| 9 | `build.bat` — PyArmor → PyInstaller → zip | `ProjectB/build.bat` |
| 10 | Teste do .exe distribuível | Manual |
