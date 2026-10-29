"""
Gera a tier list de todos os elos, em todas as rotas, como arquivos JSON estáticos.

Roda no GitHub Actions a cada 12h (.github/workflows/tierlist-snapshot.yml) e publica
o resultado na branch `tierlist-data`. O site baixa um arquivo por elo, com as 5 rotas
juntas: trocar de rota é instantâneo e ninguém espera o OP.GG montar a lista.

Uso: python backend/scripts/build_tierlist_snapshot.py <pasta-de-saída>
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from opgg_client import DEFAULT_ELO, POSITIONS, TIERLIST_ELOS, get_tierlist, get_tierlist_for_elo  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("snapshot")
logging.getLogger("httpx").setLevel(logging.WARNING)

# Os elos mais procurados primeiro: se o job for interrompido, estes já ficaram prontos.
ELO_ORDER = [
    DEFAULT_ELO, "gold", "platinum", "silver", "emerald", "diamond", "gold_plus", "platinum_plus",
    "bronze", "iron", "diamond_plus", "master_plus", "master", "grandmaster", "challenger", "all",
]


async def build(out_dir: Path) -> int:
    base = await get_tierlist()
    if base is None:
        log.error("Tier list base do OP.GG indisponível.")
        return 1

    (out_dir / "elo").mkdir(parents=True, exist_ok=True)
    index = []
    for elo in ELO_ORDER:
        started = time.time()
        results = await asyncio.gather(*[get_tierlist_for_elo(lane, elo) for lane in POSITIONS])
        positions = {lane: (r or {}).get("rows", []) for lane, r in zip(POSITIONS, results)}
        missing = [lane for lane, rows in positions.items() if not rows]
        if missing:
            log.warning(f"{elo}: sem dados para {missing}")

        payload = {
            "elo": elo,
            "label": TIERLIST_ELOS[elo],
            "ddragon_version": base["ddragon_version"],
            "updated_at": int(time.time()),
            "source": "OP.GG",
            "positions": positions,
        }
        (out_dir / "elo" / f"{elo}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        index.append({"elo": elo, "label": TIERLIST_ELOS[elo], "updated_at": payload["updated_at"],
                      "champions": sum(len(rows) for rows in positions.values())})
        log.info(f"{elo}: {index[-1]['champions']} campeões em {time.time() - started:.0f}s")

    (out_dir / "index.json").write_text(json.dumps({"generated_at": int(time.time()), "elos": index}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "tierlist-snapshot")
    sys.exit(asyncio.run(build(target)))
