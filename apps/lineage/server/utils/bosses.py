import json
import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping

from django.conf import settings


@lru_cache(maxsize=1)
def _load_bosses_index() -> Dict[str, Dict[str, str]]:
    """
    Carrega o arquivo de bosses e cria um índice por ID.
    Mantém cache em memória para evitar leituras repetidas em disco.
    """
    bosses_path = os.path.join(settings.BASE_DIR, "utils", "data", "bosses.json")
    try:
        with open(bosses_path, "r", encoding="utf-8") as handler:
            payload = json.load(handler)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    data = payload.get("data", [])
    return {str(item.get("id")): item for item in data if item.get("id") is not None}


def enrich_grandboss_status(raw_bosses: Iterable[Mapping]) -> List[Dict]:
    """
    Enriquece o resultado cru de grandboss_status com nome, nível,
    status humanizado, timestamp convertido e flag de vida.
    """
    bosses_index = _load_bosses_index()
    gmt_offset = int(getattr(settings, "GMT_OFFSET", 0))
    show_time = getattr(settings, "GRANDBOSS_SHOW_TIME", True)
    current_ts = time.time()

    enriched = []

    for entry in raw_bosses or []:
        boss_id = entry.get("boss_id")
        boss_id_str = str(boss_id) if boss_id is not None else ""
        metadata = bosses_index.get(boss_id_str, {})

        name = entry.get("name") or metadata.get("name") or f"Boss {boss_id}"
        level = entry.get("level") or metadata.get("level", "-")

        status = entry.get("status")
        respawn_human = entry.get("respawn_human")
        is_alive = entry.get("is_alive")

        raw_respawn = entry.get("respawn")
        respawn_seconds = None

        if isinstance(raw_respawn, (int, float)):
            respawn_seconds = raw_respawn / 1000 if raw_respawn > 1e12 else raw_respawn

            if respawn_seconds > current_ts:
                # Boss ainda morto, aguardando respawn
                try:
                    respawn_dt = datetime.fromtimestamp(respawn_seconds) - timedelta(hours=gmt_offset)
                    respawn_human = respawn_dt.strftime("%d/%m/%Y %H:%M") if show_time else respawn_dt.strftime("%d/%m/%Y")
                except (OSError, OverflowError, ValueError):
                    respawn_human = "-"
                status = status or "Morto"
                is_alive = False if is_alive is None else bool(is_alive)
            else:
                # Boss disponível
                respawn_human = "-" if respawn_human in (None, "") else respawn_human
                status = status or "Vivo"
                is_alive = True if is_alive is None else bool(is_alive)
        else:
            # Quando respawn vem como string ou None, manter valor textual se existir
            if respawn_human is None:
                if isinstance(raw_respawn, str) and raw_respawn.strip():
                    respawn_human = raw_respawn
                else:
                    respawn_human = "-"

            if status is None:
                status = "Desconhecido"

            if is_alive is None:
                lowered = status.lower()
                is_alive = lowered in {"vivo", "alive", "disponível", "disponivel"}

        enriched.append(
            {
                **entry,
                "boss_id": boss_id,
                "name": name,
                "level": level,
                "status": status,
                "respawn_human": respawn_human,
                "is_alive": is_alive,
                "respawn": raw_respawn,
                "respawn_seconds": respawn_seconds,
            }
        )

    return enriched


def enrich_raidboss_status(raw_bosses: Iterable[Mapping]) -> List[Dict]:
    """
    Normaliza o resultado de raidboss_status com status unificado e respawn humanizado.
    """
    gmt_offset = int(getattr(settings, "GMT_OFFSET", 0))
    show_time = getattr(settings, "RAIDBOSS_SHOW_TIME", getattr(settings, "GRANDBOSS_SHOW_TIME", True))
    current_ts = time.time()

    enriched = []

    for entry in raw_bosses or []:
        boss_id = entry.get("boss_id")
        name = entry.get("name") or f"Boss {boss_id}"
        level = entry.get("level", "-")

        status = entry.get("status")
        respawn_human = entry.get("respawn_human")
        is_alive = entry.get("is_alive")

        raw_respawn = entry.get("respawn")
        respawn_seconds = None

        if isinstance(raw_respawn, (int, float)):
            respawn_seconds = raw_respawn / 1000 if raw_respawn > 1e12 else raw_respawn

            if respawn_seconds > current_ts:
                try:
                    respawn_dt = datetime.fromtimestamp(respawn_seconds) - timedelta(hours=gmt_offset)
                    respawn_human = (
                        respawn_dt.strftime("%d/%m/%Y %H:%M") if show_time else respawn_dt.strftime("%d/%m/%Y")
                    )
                except (OSError, OverflowError, ValueError):
                    respawn_human = "-"
                status = status or "Morto"
                is_alive = False if is_alive is None else bool(is_alive)
            else:
                respawn_human = "-" if respawn_human in (None, "") else respawn_human
                status = status or "Vivo"
                is_alive = True if is_alive is None else bool(is_alive)
        else:
            if respawn_human is None:
                if isinstance(raw_respawn, str) and raw_respawn.strip():
                    respawn_human = raw_respawn
                else:
                    respawn_human = "-"

            if status is None:
                status = "Desconhecido"

            if is_alive is None:
                lowered = status.lower()
                is_alive = lowered in {"vivo", "alive", "disponível", "disponivel"}

        enriched.append(
            {
                **entry,
                "boss_id": boss_id,
                "name": name,
                "level": level,
                "status": status,
                "respawn_human": respawn_human,
                "is_alive": is_alive,
                "respawn": raw_respawn,
                "respawn_seconds": respawn_seconds,
            }
        )

    return enriched

