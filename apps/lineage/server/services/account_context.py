from __future__ import annotations

from typing import Dict, List

from django.utils.translation import gettext_lazy as _

from apps.lineage.server.models import ManagedLineageAccount
from utils.dynamic_import import get_query_class

LineageAccount = get_query_class("LineageAccount")

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

    # Sempre permite acesso à conta principal
    if normalized_login == _default_login(user):
        return True

    # Verifica se existe delegação explícita via ManagedLineageAccount
    if ManagedLineageAccount.objects.filter(
        manager_user=user,
        account_login=normalized_login,
        status=ManagedLineageAccount.Status.ACTIVE,
    ).exists():
        return True

    # Verifica se a conta está vinculada ao UUID do usuário no banco do Lineage
    user_uuid = str(user.uuid) if hasattr(user, 'uuid') else None
    if user_uuid:
        try:
            from utils.dynamic_import import get_query_class
            LineageDBClass = get_query_class("LineageDB")
            
            if LineageDBClass:
                lineage_db = LineageDBClass()
                if lineage_db and getattr(lineage_db, 'enabled', False):
                    sql = """
                        SELECT login
                        FROM accounts
                        WHERE login = :login AND linked_uuid = :uuid
                        LIMIT 1
                    """
                    try:
                        result = lineage_db.select(sql, {"login": normalized_login, "uuid": user_uuid})
                        if result and len(result) > 0:
                            return True
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Erro ao verificar acesso via linked_uuid: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao verificar acesso: {e}")

    # Verifica se o usuário é a conta mestre do e-mail e a conta tem o mesmo e-mail
    user_email = getattr(user, 'email', None)
    if user_email:
        try:
            from apps.main.home.models import EmailOwnership
            email_ownership = EmailOwnership.objects.filter(email=user_email).first()
            if email_ownership and email_ownership.owner == user:
                # Se for conta mestre, verifica se a conta do Lineage tem o mesmo e-mail
                try:
                    from utils.dynamic_import import get_query_class
                    LineageAccount = get_query_class("LineageAccount")
                    if LineageAccount and hasattr(LineageAccount, 'find_accounts_by_email'):
                        contas_por_email = LineageAccount.find_accounts_by_email(user_email)
                        for conta in contas_por_email:
                            login = conta.get("login") if isinstance(conta, dict) else getattr(conta, 'login', None)
                            if login == normalized_login:
                                return True
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Erro ao verificar acesso via e-mail: {e}")
        except Exception:
            pass

    return False


def get_available_accounts(user) -> List[Dict[str, str]]:
    """
    Retorna as contas que o usuário pode utilizar no painel.
    """
    accounts: List[Dict[str, str]] = []

    if not user or not user.is_authenticated:
        return accounts

    # SEMPRE adiciona a conta principal primeiro (username)
    default_login = _default_login(user)
    if default_login:
        accounts.append(
            {
                "login": default_login,
                "role": ManagedLineageAccount.Role.OWNER,
                "role_label": _("Conta principal"),
                "status": ManagedLineageAccount.Status.ACTIVE,
                "is_primary": True,
                "created_by": None,
            }
        )

    # Busca contas do Lineage vinculadas ao UUID do usuário
    user_uuid = str(user.uuid) if hasattr(user, 'uuid') else None
    linked_accounts = set()  # Para evitar duplicatas
    
    # Verifica se o usuário é a conta mestre do e-mail
    is_master = False
    user_email = getattr(user, 'email', None)
    if user_email:
        try:
            from apps.main.home.models import EmailOwnership
            email_ownership = EmailOwnership.objects.filter(email=user_email).first()
            if email_ownership and email_ownership.owner == user:
                is_master = True
        except Exception:
            pass
    
    if user_uuid:
        try:
            # Busca todas as contas do Lineage vinculadas ao UUID do usuário
            from utils.dynamic_import import get_query_class
            LineageDBClass = get_query_class("LineageDB")
            LineageAccount = get_query_class("LineageAccount")
            
            if LineageDBClass:
                lineage_db = LineageDBClass()
                if lineage_db and getattr(lineage_db, 'enabled', False):
                    # Se for conta mestre, busca contas por e-mail também
                    # MAS apenas as que estão vinculadas (têm linked_uuid)
                    if is_master and user_email and LineageAccount and hasattr(LineageAccount, 'find_accounts_by_email'):
                        try:
                            # Busca todas as contas do Lineage com o mesmo e-mail
                            contas_por_email = LineageAccount.find_accounts_by_email(user_email)
                            for conta in contas_por_email:
                                login = conta.get("login") if isinstance(conta, dict) else getattr(conta, 'login', None)
                                linked_uuid = conta.get("linked_uuid") if isinstance(conta, dict) else getattr(conta, 'linked_uuid', None)
                                
                                # Só adiciona se tiver linked_uuid definido (está vinculada)
                                if login and login != default_login and linked_uuid:
                                    linked_accounts.add(login)
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Erro ao buscar contas por e-mail: {e}")
                    
                    # Busca contas vinculadas ao UUID do usuário
                    sql = """
                        SELECT login
                        FROM accounts
                        WHERE linked_uuid = :uuid
                    """
                    try:
                        result = lineage_db.select(sql, {"uuid": user_uuid})
                        if result:
                            for row in result:
                                # Tenta diferentes formas de acessar o login
                                login = None
                                if isinstance(row, dict):
                                    login = row.get("login")
                                elif hasattr(row, 'login'):
                                    login = getattr(row, 'login', None)
                                elif hasattr(row, '__getitem__'):
                                    try:
                                        login = row['login']
                                    except (KeyError, TypeError):
                                        pass
                                
                                if login and login != default_login:  # Evita duplicar a conta principal
                                    linked_accounts.add(login)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Erro ao buscar contas vinculadas por UUID: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao inicializar LineageDB: {e}")

    # Adiciona contas do Lineage vinculadas ao UUID do usuário
    for login in linked_accounts:
        accounts.append(
            {
                "login": login,
                "role": ManagedLineageAccount.Role.OWNER,
                "role_label": _("Conta vinculada"),
                "status": ManagedLineageAccount.Status.ACTIVE,
                "is_primary": False,
                "created_by": None,
            }
        )

    # Adiciona contas delegadas via ManagedLineageAccount
    try:
        links = ManagedLineageAccount.objects.filter(
            manager_user=user, status=ManagedLineageAccount.Status.ACTIVE
        ).select_related("created_by")

        for link in links:
            # Evita adicionar se já estiver na lista
            if not any(acc["login"] == link.account_login for acc in accounts):
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
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erro ao buscar contas delegadas: {e}")

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

