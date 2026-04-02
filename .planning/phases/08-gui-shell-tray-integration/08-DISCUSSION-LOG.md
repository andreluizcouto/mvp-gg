# Phase 8: GUI Shell + Tray Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 08-gui-shell-tray-integration
**Areas discussed:** Window Appearance, Close-to-Tray Behavior, Tray Interaction, Window Position/Size

---

## Window Appearance

### Q1: Window Size/Proportion

| Option | Description | Selected |
|--------|-------------|----------|
| Compacto 400x500 | Painel lateral, só status e settings | |
| Médio 600x700 | Status + activity log + settings | |
| Maior 800x600 | Layout horizontal com sidebar | |
| Você decide | O que fizer sentido para o conteúdo | ✓ |

**User's choice:** Agent's discretion — pick what makes sense for the content
**Notes:** None

### Q2: Branding

| Option | Description | Selected |
|--------|-------------|----------|
| Logo/ícone no topo | Usar o logo do mvp.gg no topo da janela | ✓ |
| Texto simples | Só nome "MVPApp" estilizado | |
| Sem branding | Janela limpa, só conteúdo | |

**User's choice:** Logo no topo da janela
**Notes:** Logo está em `C:\Users\andre\Desktop\mvp-gg\mvpgg.png` (não em favicon.svg)

### Q3: Color Scheme

| Option | Description | Selected |
|--------|-------------|----------|
| Dark padrão CTk | Cinza escuro #2b2b2b | ✓ |
| Escuro + gold | Remete ao LoL (#c8aa6e) | |
| Escuro + azul | Tom tech/limpo | |

**User's choice:** Esquema escuro padrão do CustomTkinter

---

## Close-to-Tray Behavior

### Q4: Feedback ao Minimizar

| Option | Description | Selected |
|--------|-------------|----------|
| Fechar silenciosamente | Sem aviso | |
| Tooltip só na primeira vez | "MVPApp continua rodando no tray" | |
| Sempre mostrar notificação | Notificação toda vez | |

**User's choice:** Mostrar sempre, mas com botão "não falar novamente"
**Notes:** Notificação tray + opção de suprimir persistida em config

---

## Tray Interaction

### Q5: Restore Method

| Option | Description | Selected |
|--------|-------------|----------|
| Double-click | Comportamento padrão Windows | ✓ |
| Single-click | | |
| Ambos | | |

**User's choice:** Double-click — padrão Windows

### Q6: Menu "Abrir MVPApp"

| Option | Description | Selected |
|--------|-------------|----------|
| Sim — adicionar ao menu | Além do double-click | ✓ |
| Não — double-click suficiente | | |

**User's choice:** Adicionar "Abrir MVPApp" ao menu do tray

---

## Window Position/Size

### Q7: Resizable

| Option | Description | Selected |
|--------|-------------|----------|
| Tamanho fixo | Não pode redimensionar | ✓ |
| Resizável com mínimo | Flexível | |

**User's choice:** Tamanho fixo

### Q8: Position

| Option | Description | Selected |
|--------|-------------|----------|
| Centralizar na tela | Recomendado | ✓ |
| Lembrar última posição | Persiste em config | |
| Canto inferior direito | Perto do tray | |

**User's choice:** Centralizar na tela

---

## Agent's Discretion

- Window dimensions
- Dark mode configuration method
- Window titlebar icon format
- Show/hide animation

## Deferred Ideas

None
