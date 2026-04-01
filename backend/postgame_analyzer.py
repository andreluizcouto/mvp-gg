"""
Analise pos-game: monta prompt batch com todos os prints + dados da API
e faz 1 chamada de IA para gerar o coaching completo.
"""
import base64
import logging
import os
import re
from typing import Optional

from analysis_contracts import AnalysisEvidenceBundle

logger = logging.getLogger(__name__)

_PROMPT_INJECTION_RE = re.compile(
    r"(ignore\s+(all\s+)?previous|###\s*system|<\|im_sep\|>|<\|endoftext\|>|\[INST\]|\[/INST\])",
    re.IGNORECASE,
)


def _sanitize(text: str) -> str:
    """Remove sequencias que podem ser usadas para prompt injection."""
    return _PROMPT_INJECTION_RE.sub("", text).strip()


def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def build_batch_prompt(events: list[dict], match_context: str, num_images: int) -> str:
    """Monta o prompt completo para analise batch pos-game."""
    lines = []
    lines.append("Voce e um coach de alto elo revisando o replay de um aluno.")
    lines.append("Abaixo estao os dados da partida e prints do minimapa em cada evento. Imagens em ordem cronologica (1 a " + str(num_images) + ").")
    lines.append("")

    if match_context:
        lines.append("## Dados da partida (Riot API)")
        lines.append(_sanitize(match_context))
        lines.append("")

    lines.append("## Eventos capturados")
    lines.append("")

    death_count = 0
    for i, evt in enumerate(events):
        time_str = _format_time(evt.get("game_time_sec", 0))
        etype = evt.get("event_type", "")
        detail = _sanitize(evt.get("detail", ""))
        champion = evt.get("champion", "")

        if etype == "death":
            death_count += 1
            killer = _sanitize(evt.get("killer", "desconhecido"))
            assisters = [_sanitize(a) for a in evt.get("assisters", [])]
            assist_str = f" (assist: {', '.join(assisters)})" if assisters else ""
            lines.append(f"**Imagem {i+1}** [{time_str}] Morte #{death_count}: {champion} morto por {killer}{assist_str}")
        elif etype == "kill":
            victim = _sanitize(evt.get("victim", "desconhecido"))
            assisters = [_sanitize(a) for a in evt.get("assisters", [])]
            assist_str = f" (assist: {', '.join(assisters)})" if assisters else ""
            lines.append(f"**Imagem {i+1}** [{time_str}] Kill: {champion} matou {victim}{assist_str}")
        elif etype == "multikill":
            lines.append(f"**Imagem {i+1}** [{time_str}] {detail}: {champion}")
        else:
            lines.append(f"**Imagem {i+1}** [{time_str}] {detail}")

    lines.append("")
    lines.append("## Como analisar")
    lines.append("")
    lines.append("REGRAS DE ESTILO — OBRIGATORIO:")
    lines.append("- Escreva como um coach falando com o aluno, nao como um relatorio de IA.")
    lines.append("- Use linguagem natural e direta, como se estivesse numa call de coaching.")
    lines.append("- NAO use tabelas markdown, NAO use emojis, NAO use headers com ##.")
    lines.append("- NAO faca listas com bullet points repetitivos no mesmo formato.")
    lines.append("- Varie a estrutura das frases. Misture frases curtas e longas.")
    lines.append("- Quando criticar, explique O QUE o jogador deveria ter feito em vez disso.")
    lines.append("- Evite frases genericas tipo 'posicionamento isolado em teamfight' — seja especifico sobre onde e por que.")
    lines.append("")
    lines.append("REGRAS DE CONTEUDO:")
    lines.append("- Para cada MORTE: olhe o minimapa no print. O que estava visivel que o jogador ignorou? Onde ele deveria estar?")
    lines.append("- Para cada KILL: o risco valeu a pena? Teve sorte ou foi bem jogado?")
    lines.append("- OBJETIVOS: os dados ja dizem qual time pegou cada objetivo (aliado/inimigo). Use essa informacao — NAO invente que foi roubado se nao esta marcado como ROUBADO nos dados.")
    lines.append("- Identifique padroes entre as mortes (ex: sempre morria sem ward, sempre isolado, etc).")
    lines.append("- IMPORTANTE: use NOMES DE CHAMPIONS (ex: Lucian, Thresh), nunca nicks de jogador.")
    lines.append("")
    lines.append("Termine com 2-3 frases de conselho pratico para a proxima partida.")
    lines.append("Baseie-se apenas no que e visivel nos prints e nos dados acima.")

    return "\n".join(lines)


def _match_context_from_bundle(bundle: AnalysisEvidenceBundle) -> str:
    """Builds a readable match-context block from normalized bundle fields."""

    lines: list[str] = []
    lines.append(f"source: {bundle.source.value}")
    lines.append(f"match_id: {bundle.match_id}")
    if bundle.match_context is not None:
        lines.append(f"player: {bundle.match_context.player_riot_id}")
        lines.append(f"champion: {bundle.match_context.player_champion}")
        lines.append(f"role: {bundle.match_context.role}")
        lines.append(f"kda: {bundle.match_context.kda}")
        lines.append(f"cs_per_min: {bundle.match_context.cs_per_min}")
        lines.append(f"vision_score: {bundle.match_context.vision_score}")
        lines.append(f"duration_min: {bundle.match_context.duration_min}")
        lines.append(f"rank: {bundle.match_context.rank}")
    if bundle.analysis_payload:
        lines.append(f"metadata: {bundle.analysis_payload}")
    return "\n".join(lines)


def _load_image_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


async def analyze_postgame(
    events: list[dict] | None = None,
    image_paths: list[str] | None = None,
    match_context: str = "",
    bundle: AnalysisEvidenceBundle | None = None,
) -> str:
    """
    Analise batch pos-game: envia todos os prints + prompt unico para a IA.
    Tenta Gemini primeiro, fallback para Haiku.
    """
    resolved_events = list(events or [])
    resolved_image_paths = list(image_paths or [])
    resolved_match_context = match_context

    if bundle is not None:
        if not resolved_events and bundle.local_events:
            resolved_events = [evt.model_dump(exclude={"minimap_base64"}) for evt in bundle.local_events]
        if not resolved_image_paths and bundle.image_paths:
            resolved_image_paths = list(bundle.image_paths)
        if not resolved_match_context:
            resolved_match_context = _match_context_from_bundle(bundle)

    prompt = build_batch_prompt(resolved_events, resolved_match_context, num_images=len(resolved_image_paths))
    image_bytes_list = [_load_image_bytes(p) for p in resolved_image_paths]

    try:
        result = await _call_gemini_batch(image_bytes_list, prompt)
        logger.info("Analise pos-game via Gemini Flash")
        return result
    except Exception as e:
        logger.warning(f"Gemini falhou ({e}), usando Haiku para pos-game")

    result = await _call_haiku_batch(image_bytes_list, prompt)
    logger.info("Analise pos-game via Claude Haiku")
    return result


async def _call_gemini_batch(images: list[bytes], prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    parts = []
    for img_bytes in images:
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
    parts.append(types.Part.from_text(text=prompt))

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=[types.Content(parts=parts)],
    )
    return response.text


async def _call_haiku_batch(images: list[bytes], prompt: str) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurada — adicione nas variáveis de ambiente do Render")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    content = []
    for img_bytes in images:
        b64 = base64.b64encode(img_bytes).decode()
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
    content.append({"type": "text", "text": prompt})

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text
