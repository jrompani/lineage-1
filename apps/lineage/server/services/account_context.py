from __future__ import annotations

from typing import Dict, List

from django.utils.translation import gettext_lazy as _

from apps.lineage.server.models import ManagedLineageAccount

SESSION_KEY = "lineage_active_login"


def _normalize_login(login: str) -> str:
    return (login or "").strip()


def _default_login(user) -> str:
    return getattr(user, "username", "")


def user_has_access(user, account_login: str) -> bool:
    """
    Verifica se o usuário tem permissão para operar na conta informada.
    """
    if not user or not user.is_authenticated:
        return False

    normalized_login = _normalize_login(account_login)
    if not normalized_login:
        return False

    if normalized_login == _default_login(user):
        return True

    return ManagedLineageAccount.objects.filter(
        manager_user=user,
        account_login=normalized_login,
        status=ManagedLineageAccount.Status.ACTIVE,
    ).exists()


def get_available_accounts(user) -> List[Dict[str, str]]:
    """
    Retorna as contas que o usuário pode utilizar no painel.
    """
    accounts: List[Dict[str, str]] = []

    if not user or not user.is_authenticated:
        return accounts

    accounts.append(
        {
            "login": _default_login(user),
            "role": ManagedLineageAccount.Role.OWNER,
            "role_label": _("Conta principal"),
            "status": ManagedLineageAccount.Status.ACTIVE,
            "is_primary": True,
            "created_by": None,
        }
    )

    links = ManagedLineageAccount.objects.filter(
        manager_user=user, status=ManagedLineageAccount.Status.ACTIVE
    ).select_related("created_by")

    for link in links:
        accounts.append(
            {
                "login": link.account_login,
                "role": link.role,
                "role_label": link.get_role_display(),
                "status": link.status,
                "is_primary": False,
                "created_by": link.created_by.username if link.created_by else None,
            }
        )

    return accounts


def get_active_login(request) -> str:
    """
    Obtém a conta ativa armazenada na sessão. Caso o usuário não tenha acesso
    a ela, retorna a conta padrão (username) e atualiza a sessão.
    """
    stored_login = _normalize_login(request.session.get(SESSION_KEY, ""))
    if stored_login and user_has_access(request.user, stored_login):
        return stored_login

    fallback = _default_login(request.user)
    request.session[SESSION_KEY] = fallback
    request.session.modified = True
    return fallback


def set_active_login(request, account_login: str):
    """
    Define explicitamente a conta ativa do usuário, validando o acesso.
    """
    normalized_login = _normalize_login(account_login)
    if not user_has_access(request.user, normalized_login):
        raise PermissionError(_("Você não tem acesso a esta conta."))

    request.session[SESSION_KEY] = normalized_login
    request.session.modified = True


def clear_active_login(request):
    """
    Remove a conta ativa da sessão.
    """
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
        request.session.modified = True


def get_lineage_template_context(request) -> Dict[str, object]:
    """
    Constrói um dicionário padrão para ser usado nos templates com informações
    sobre a conta ativa e as contas disponíveis.
    """
    email_master_owner = None
    is_email_master_owner = True
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False) and hasattr(user, "get_email_master_owner"):
        email_master_owner = user.get_email_master_owner()
        is_email_master_owner = (email_master_owner is None) or (email_master_owner == user)

    return {
        "active_account_login": get_active_login(request),
        "available_lineage_accounts": get_available_accounts(request.user),
        "email_master_owner": email_master_owner,
        "is_email_master_owner": is_email_master_owner,
    }

