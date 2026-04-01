# Features Research

**Project:** mvp.gg
**Domain:** League of Legends statistics plus AI post-game analysis
**Researched:** 2026-04-01
**Confidence:** MEDIUM

## Feature Categories

### Player Lookup and Match Discovery

**Table stakes**
- Search by Riot ID
- Recent match history
- Clear rank and match metadata
- Fast navigation from profile to match page

**Competitive value**
- Coaching availability states per match
- Fast re-entry into previously analyzed matches

### Match Understanding

**Table stakes**
- Scoreboard and participant data
- Builds, runes, summoner spells, and outcome context
- Timeline-backed performance context

**Competitive value**
- Evidence-backed AI interpretation instead of raw stats only
- Highlighted mistakes, strengths, and improvement points tied to the actual match

### Trust and Product Quality

**Table stakes**
- Stable analysis status handling
- Clear failure and pending states
- Secure backend handling of sensitive flows

**Competitive value**
- Confidence-building UX that explains why the analysis is trustworthy
- Reliable enough outputs that players want to share the product with others

### Deferred Differentiators

- Dynamic chat with the AI about a match
- Comparison against reference matches or higher-ranked players
- Deep phase-of-game coaching
- Live coaching during the match
- Team or coach workflows

## Product Positioning

The product should not try to win by copying every stat feature from established tracker sites. The win condition for v1 is a smaller, sharper promise: show a solo queue player what actually mattered in their game and what to fix next.

## Implications

- Requirements should focus on trust, consistency, and evidence-backed coaching rather than feature count.
- Roadmap phases should separate backend evidence quality from frontend presentation so the team can improve signal before polishing delivery.

## Sources

### Primary
- Riot Developer Portal: Match-V5 API reference
  https://developer.riotgames.com/apis#match-v5

### Secondary
- User-provided product goals and brownfield architecture notes in `.planning/PROJECT.md`
- Existing codebase map in `.planning/codebase/`

---
*Research completed: 2026-04-01*
