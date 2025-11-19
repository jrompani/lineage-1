from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from django.utils.translation import gettext_lazy as _

from apps.main.home.models import PerfilGamer, ConquistaUsuario


@dataclass
class RewardTier:
    slug: str
    name: str
    description: str
    threshold: int
    gradient: str


def _build_tier(progression: int, tiers: List[RewardTier]) -> Dict[str, Any]:
    tiers_sorted = sorted(tiers, key=lambda tier: tier.threshold)
    current = tiers_sorted[0]

    for tier in tiers_sorted:
        if progression >= tier.threshold:
            current = tier
        else:
            break

    next_tier = next((tier for tier in tiers_sorted if tier.threshold > progression), None)
    return {
        "current": current,
        "next": next_tier,
    }


def _build_requirements_status(requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
    completed = sum(1 for requirement in requirements if requirement["met"])
    total = len(requirements)
    progress_percent = int((completed / total) * 100) if total else 0
    next_requirement = next((req for req in requirements if not req["met"]), None)

    return {
        "requirements": requirements,
        "completed": completed,
        "total": total,
        "progress_percent": progress_percent,
        "next_requirement": next_requirement,
    }


def build_profile_rewards_context(user) -> Dict[str, Any]:
    """
    Constrói o contexto usado para mostrar progresso de recompensas
    de borda de avatar e capa de perfil na tela /app/profile/.
    """
    perfil, created = PerfilGamer.objects.get_or_create(user=user)
    conquistas_desbloqueadas = ConquistaUsuario.objects.filter(usuario=user).count()

    # Avatar border reward logic
    avatar_requirements = _build_requirements_status([
        {
            "label": _("Verifique seu e-mail"),
            "description": _("Libera partículas brilhantes na borda."),
            "met": user.is_email_verified,
        },
        {
            "label": _("Ative o 2FA"),
            "description": _("Garante um efeito de escudo animado."),
            "met": user.is_2fa_enabled,
        },
        {
            "label": _("Complete nome e biografia"),
            "description": _("Desbloqueia luz pulsante personalizada."),
            "met": bool(user.first_name and user.last_name and user.bio),
        },
        {
            "label": _("Adicione um endereço"),
            "description": _("Gera textura holográfica na borda."),
            "met": user.addresses.exists(),
        },
        {
            "label": _("Alcance nível 5"),
            "description": _("Transforma a borda em um anel lendário."),
            "met": perfil.level >= 5,
        },
    ])

    avatar_tiers = [
        RewardTier(
            slug="base",
            name=_("Borda Pulsar"),
            description=_("Borda padrão com brilho suave."),
            threshold=0,
            gradient="linear-gradient(135deg, #adb5bd, #ced4da)",
        ),
        RewardTier(
            slug="silver",
            name=_("Borda Prisma"),
            description=_("Efeito prateado com partículas discretas."),
            threshold=2,
            gradient="linear-gradient(135deg, #dee2ff, #adb5ff)",
        ),
        RewardTier(
            slug="gold",
            name=_("Borda Aurora"),
            description=_("Mistura dourada com brilho constante."),
            threshold=4,
            gradient="linear-gradient(135deg, #ffd166, #f0772b)",
        ),
        RewardTier(
            slug="mythic",
            name=_("Borda Cosmos"),
            description=_("Anel lendário com animação nebulosa."),
            threshold=5,
            gradient="linear-gradient(135deg, #845ef7, #22b8cf)",
        ),
    ]

    avatar_tier_info = _build_tier(avatar_requirements["completed"], avatar_tiers)

    # Profile cover reward logic
    cover_requirements = _build_requirements_status([
        {
            "label": _("Chegue ao nível 10"),
            "description": _("Desbloqueia gradiente dinâmico."),
            "met": perfil.level >= 10,
        },
        {
            "label": _("Desbloqueie 5 conquistas"),
            "description": _("Libera textura animada especial."),
            "met": conquistas_desbloqueadas >= 5,
        },
        {
            "label": _("Escreva uma biografia"),
            "description": _("Permite sobreposição com assinatura."),
            "met": bool(user.bio),
        },
        {
            "label": _("Ative conta verificada social"),
            "description": _("Garante efeito exclusivo de constelação."),
            "met": user.social_verified or user.is_verified_account,
        },
    ])

    cover_tiers = [
        RewardTier(
            slug="starter",
            name=_("Capa Aurora Básica"),
            description=_("Capa translúcida com partículas suaves."),
            threshold=0,
            gradient="linear-gradient(135deg, #c3cfe2, #f5f7fa)",
        ),
        RewardTier(
            slug="stellar",
            name=_("Capa Nebulosa"),
            description=_("Neblina colorida com brilho em loop."),
            threshold=2,
            gradient="linear-gradient(135deg, #8e9eab, #eef2f3)",
        ),
        RewardTier(
            slug="celestial",
            name=_("Capa Horizonte"),
            description=_("Gradiente escuro com detalhes neon."),
            threshold=3,
            gradient="linear-gradient(135deg, #355c7d, #6c5b7b, #c06c84)",
        ),
        RewardTier(
            slug="mythic",
            name=_("Capa Constelação"),
            description=_("Painel cósmico com estrelas animadas."),
            threshold=4,
            gradient="linear-gradient(135deg, #0f2027, #203a43, #2c5364)",
        ),
    ]

    cover_tier_info = _build_tier(cover_requirements["completed"], cover_tiers)

    return {
        "avatar_reward": {
            "title": _("Borda do Avatar"),
            "requirements": avatar_requirements["requirements"],
            "progress_percent": avatar_requirements["progress_percent"],
            "completed": avatar_requirements["completed"],
            "total": avatar_requirements["total"],
            "current_tier": avatar_tier_info["current"],
            "next_tier": avatar_tier_info["next"],
            "next_requirement": avatar_requirements["next_requirement"],
        },
        "cover_reward": {
            "title": _("Capa de Perfil"),
            "requirements": cover_requirements["requirements"],
            "progress_percent": cover_requirements["progress_percent"],
            "completed": cover_requirements["completed"],
            "total": cover_requirements["total"],
            "current_tier": cover_tier_info["current"],
            "next_tier": cover_tier_info["next"],
            "next_requirement": cover_requirements["next_requirement"],
        },
    }


