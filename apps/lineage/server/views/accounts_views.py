from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.main.home.decorator import conditional_otp_required
from ..decorators import require_lineage_connection
from datetime import datetime
from django.utils.timezone import make_aware
from django.utils.timezone import now
from utils.resources import gen_avatar, get_class_name
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_POST
from apps.main.home.tasks import send_email_task
from apps.main.home.models import User
from apps.lineage.server.lineage_account_manager import LineageAccount
from apps.lineage.server.models import ManagedLineageAccount
from apps.lineage.server.services.account_context import (
    get_active_login,
    get_available_accounts,
    get_lineage_template_context,
    set_active_login,
    user_has_access,
)
from utils.dynamic_import import get_query_class
from django.utils.translation import gettext as _

signer = TimestampSigner()

LineageServices = get_query_class("LineageServices")


@conditional_otp_required
@require_lineage_connection
def account_dashboard(request):
    active_login = get_active_login(request)
    account_data = LineageAccount.check_login_exists(active_login)

    if not account_data or len(account_data) == 0:
        if active_login == request.user.username:
            return redirect('server:lineage_register')
        messages.error(request, "Conta do Lineage não encontrada.")
        return redirect('server:manage_lineage_accounts')

    account = account_data[0]
    owner_uuid = account.get("linked_uuid")
    user_uuid = str(request.user.uuid)
    is_owner = owner_uuid == user_uuid

    if not owner_uuid:
        messages.warning(request, "Essa conta ainda não está vinculada a nenhum usuário do painel. Solicite ao proprietário para concluir o processo.")
        return redirect('server:manage_lineage_accounts')

    if not is_owner and not user_has_access(request.user, active_login):
        messages.error(request, "Você não tem permissão para visualizar essa conta.")
        return redirect('server:manage_lineage_accounts')

    try:
        personagens = LineageServices.find_chars(active_login)
    except Exception:
        personagens = []
        messages.warning(request, 'Não foi possível carregar seus personagens agora.')

    acesslevel = LineageAccount.get_acess_level()
    account['status'] = "Ativa" if int(account[acesslevel]) >= 0 else "Bloqueada"

    created_time = None
    if account.get('created_time'):
        try:
            created_time = make_aware(datetime.strptime(account['created_time'], '%Y-%m-%d %H:%M:%S'))
        except:
            try:
                created_time = make_aware(datetime.fromtimestamp(int(account['created_time'])))
            except:
                created_time = None

    char_list = []
    for char in personagens:
        level = char.get('base_level', '-')
        obj_id = char.get('obj_id') or char.get('obj_Id') or char.get('charId') or char.get('char_id', '-')
        char_name = char.get('char_name') or char.get('charname', '-')
        base_class = char.get('base_class') or char.get('classid', 0)
        sex = char.get('sex', 0)

        char_list.append({
            'id': obj_id,
            'nome': char_name,
            'title': char.get('title', '-'),
            'lastAccess': datetime.fromtimestamp(int(char['lastAccess']) / 1000).strftime('%B %d, %Y às %H:%M') if char.get('lastAccess') else '-',
            'online': 'Online' if char.get('online') else 'Offline',
            'base_class': get_class_name(base_class),
            'subclass1': get_class_name(char['subclass1']) if char.get('subclass1') else '-',
            'subclass2': get_class_name(char['subclass2']) if char.get('subclass2') else '-',
            'subclass3': get_class_name(char['subclass3']) if char.get('subclass3') else '-',
            'level': level,
            'sex': 'Feminino' if sex else 'Masculino',
            'pvp': char.get('pvpkills', 0),
            'pk': char.get('pkkills', 0),
            'karma': char.get('karma', 0),
            'clan': char.get('clan_name', '-'),
            'ally': char.get('ally_name', '-'),
            'nobless': 'Sim' if char.get('nobless') else 'Não',
            'hero': 'Sim' if char.get('hero_end') and int(char['hero_end']) > int(now().timestamp() * 1000) else 'Não',
            'avatar': gen_avatar(base_class, sex)
        })

    context = {
        'account': account,
        'created_time': created_time.strftime('%B %d, %Y às %H:%M') if created_time else '-',
        'lastIP': account.get('lastIP', '-'),
        'characters': char_list,
        'char_count': len(char_list),
        'is_owner_account': is_owner,
    }
    context.update(get_lineage_template_context(request))

    return render(request, 'l2_accounts/dashboard.html', context)


@conditional_otp_required
@require_lineage_connection
def update_password(request):
    user = request.user

    # Verifica se a conta Lineage está vinculada
    account_data = LineageAccount.check_login_exists(user.username)
    if not account_data or len(account_data) == 0 or not account_data[0].get("linked_uuid"):
        messages.error(request, "Sua conta Lineage não está vinculada. Por favor, vincule sua conta antes de atualizar a senha.")
        return redirect('server:link_lineage_account')
    
    user_uuid = str(request.user.uuid)
    if account_data[0].get("linked_uuid") != user_uuid:
        messages.error(request, "Sua conta Lineage está vinculada a outro usuário. Por favor, vincule novamente sua conta corretamente.")
        return redirect('server:link_lineage_account')

    if request.method == "POST":
        senha = request.POST.get("nova_senha")
        confirmar = request.POST.get("confirmar_senha")

        if not senha or not confirmar:
            messages.error(request, "Por favor, preencha todos os campos.")
            return redirect('server:update_password')

        if senha != confirmar:
            messages.error(request, "As senhas não coincidem.")
            return redirect('server:update_password')

        success = LineageAccount.update_password(senha, user.username)

        if success:
            messages.success(request, "Senha atualizada com sucesso!")
            return redirect('server:account_dashboard')
        else:
            messages.error(request, "Erro ao atualizar senha.")
            return redirect('server:update_password')

    # GET request — exibe o formulário
    return render(request, "l2_accounts/update_password.html")


@conditional_otp_required
@require_lineage_connection
def register_lineage_account(request):
    user = request.user

    # Verifica se a conta já existe
    existing_account = LineageAccount.check_login_exists(user.username)
    if existing_account and len(existing_account) > 0:
        messages.info(request, "Sua conta Lineage já está criada.")
        return redirect('server:account_dashboard')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        if password != confirm:
            messages.error(request, "As senhas não coincidem.")
            return redirect('server:lineage_register')

        success = LineageAccount.register(
            login=user.username,
            password=password,
            access_level=0,
            email=user.email
        )

        if success:
            # Vincula automaticamente a conta após o registro
            user_uuid = str(request.user.uuid)  # Certifique-se de que o User tem um campo `uuid`
            success_link = LineageAccount.link_account_to_user(user.username, user_uuid)

            if success_link:
                messages.success(request, "Conta Lineage criada e vinculada com sucesso!")
                return redirect('server:register_success')
            else:
                messages.error(request, "Erro ao vincular a conta.")
                return redirect('server:lineage_register')
        else:
            messages.error(request, "Erro ao criar conta.")
            return redirect('server:lineage_register')

    return render(request, 'l2_accounts/register.html', {
        'login': user.username,
        'email': user.email
    })


@conditional_otp_required
@require_lineage_connection
def register_success(request):
    return render(request, 'l2_accounts/register_success.html')


@conditional_otp_required
@require_lineage_connection
def link_lineage_account(request):
    if request.method == "POST":
        login_jogo = request.user.username
        senha_jogo = request.POST.get("senha")

        # Verifica se login + senha são válidos
        is_valided = LineageAccount.validate_credentials(login_jogo, senha_jogo)
        if not is_valided:
            messages.error(request, "Login ou senha incorretos.")
            return redirect("server:link_lineage_account")
        
        conta = LineageAccount.get_account_by_login(login_jogo)

        # Já está vinculada?
        if conta.get("linked_uuid"):
            messages.warning(request, "Essa conta já está vinculada a outro usuário.")
            return redirect("server:link_lineage_account")

        # Vincula a conta
        user_uuid = str(request.user.uuid)  # Certifique-se de que o User tem um campo `uuid`
        success = LineageAccount.link_account_to_user(login_jogo, user_uuid)

        if success:
            messages.success(request, "Conta vinculada com sucesso!")
            return redirect("server:account_dashboard")
        else:
            messages.error(request, "Erro ao vincular conta.")
            return redirect("server:link_lineage_account")

    return render(request, "l2_accounts/vincular_conta.html")


@conditional_otp_required
@require_lineage_connection
def request_link_by_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            messages.error(request, "Informe um e-mail.")
            return redirect("server:request_link_by_email")

        # Verifica se existe uma conta com esse email e ainda não vinculada
        contas = LineageAccount.find_accounts_by_email(email)
        conta = next((c for c in contas if not c.get("linked_uuid")), None)

        if not conta:
            messages.error(request, "Nenhuma conta não vinculada foi encontrada com esse e-mail.")
            return redirect("server:request_link_by_email")

        # Cria token assinado
        data = f"{conta['login']}|{email}"
        token = signer.sign(data)

        link = request.build_absolute_uri(
            reverse("server:link_by_email_token", args=[token])
        )

        # Envia e-mail
        send_email_task.delay(
            "Vinculação de Conta Lineage",
            f"Clique no link abaixo para vincular sua conta:\n\n{link}\n\nO link expira em 1 hora.",
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )

        messages.success(request, "Um link de verificação foi enviado para o seu e-mail.")
        return redirect("server:request_link_by_email")

    return render(request, "l2_accounts/link_by_email_request.html")


@conditional_otp_required
@require_lineage_connection
def link_by_email_token(request, token):
    try:
        data = signer.unsign(token, max_age=3600)  # 1 hora
        login, email = data.split('|')
    except SignatureExpired:
        messages.error(request, "Este link expirou. Solicite um novo.")
        return redirect("server:request_link_by_email")
    except BadSignature:
        messages.error(request, "Token inválido.")
        return redirect("server:request_link_by_email")

    conta = LineageAccount.get_account_by_login_and_email(login, email)
    if not conta or conta.get("linked_uuid"):
        messages.error(request, "Conta inválida ou já vinculada.")
        return redirect("server:link_lineage_account")
    
    success = LineageAccount.link_account_to_user(login, str(request.user.uuid))
    if success:
        messages.success(request, "Conta vinculada com sucesso!")
        return redirect("server:account_dashboard")
    else:
        messages.error(request, "Erro ao vincular a conta.")
        return redirect("server:link_lineage_account")


@conditional_otp_required
@require_lineage_connection
def manage_lineage_accounts(request):
    # Contas delegadas pelo usuário atual (delegações explícitas)
    delegated_links = ManagedLineageAccount.objects.filter(
        created_by=request.user
    ).select_related("manager_user").order_by("account_login")

    # Contas delegadas para o usuário atual (delegações explícitas)
    links_as_manager = ManagedLineageAccount.objects.filter(
        manager_user=request.user,
        status=ManagedLineageAccount.Status.ACTIVE,
    ).select_related("created_by").order_by("account_login")

    # Busca contas vinculadas automaticamente (via linked_uuid ou e-mail)
    # que não estão em ManagedLineageAccount
    linked_accounts_info = []
    available_accounts = get_available_accounts(request.user)
    
    # Lista de logins que já estão em links_as_manager para evitar duplicatas
    delegated_logins = {link.account_login for link in links_as_manager}
    
    for account in available_accounts:
        # Se a conta não é a principal e não tem created_by (não foi delegada explicitamente)
        if not account.get("is_primary") and not account.get("created_by"):
            login = account.get("login")
            role_label = account.get("role_label", "")
            
            # Verifica se já existe um ManagedLineageAccount para esta conta
            existing_link = ManagedLineageAccount.objects.filter(
                account_login=login,
                created_by=request.user
            ).first()
            
            # Se não existe delegação explícita e não está na lista de delegadas, adiciona
            if not existing_link and login and login not in delegated_logins:
                linked_accounts_info.append({
                    "account_login": login,
                    "role_label": role_label,
                    "is_linked": True,  # Marca como vinculada automaticamente
                })

    context = get_lineage_template_context(request)
    context.update(
        {
            "delegated_links": delegated_links,
            "links_as_manager": links_as_manager,
            "linked_accounts_info": linked_accounts_info,  # Contas vinculadas automaticamente
            "total_delegated_accounts": len(links_as_manager) + len(linked_accounts_info),
        }
    )
    return render(request, "l2_accounts/manage_accounts.html", context)


@conditional_otp_required
@require_lineage_connection
@require_POST
def add_contra_mestre(request):
    if not request.user.is_email_master_owner:
        owner = request.user.get_email_master_owner()
        if owner and owner != request.user:
            messages.error(
                request,
                _("Somente a conta mestre %(owner)s pode delegar acessos com este e-mail.") % {"owner": owner.username},
            )
        else:
            messages.error(request, _("Você não tem permissão para delegar acessos."))
        return redirect("server:manage_lineage_accounts")

    account_login = (request.POST.get("account_login") or "").strip()
    manager_username = (request.POST.get("manager_username") or "").strip()
    notes = (request.POST.get("notes") or "").strip()

    if not account_login or not manager_username:
        messages.error(request, "Informe o login da conta e o usuário do contra mestre.")
        return redirect("server:manage_lineage_accounts")

    if manager_username == request.user.username:
        messages.error(request, "Informe o usuário do contra mestre, não o seu.")
        return redirect("server:manage_lineage_accounts")

    try:
        manager_user = User.objects.get(username=manager_username)
    except User.DoesNotExist:
        messages.error(request, "Usuário informado não foi encontrado.")
        return redirect("server:manage_lineage_accounts")

    conta = LineageAccount.get_account_by_login(account_login)
    if not conta:
        messages.error(request, "Conta do Lineage não encontrada.")
        return redirect("server:manage_lineage_accounts")

    if conta.get("linked_uuid") != str(request.user.uuid):
        messages.error(request, "Apenas o proprietário da conta pode delegar contra mestres.")
        return redirect("server:manage_lineage_accounts")

    link, created = ManagedLineageAccount.objects.update_or_create(
        account_login=account_login,
        manager_user=manager_user,
        defaults={
            "created_by": request.user,
            "role": ManagedLineageAccount.Role.CONTRA_MESTRE,
            "status": ManagedLineageAccount.Status.ACTIVE,
            "notes": notes,
        },
    )

    if created:
        messages.success(request, f"Usuário {manager_username} agora pode gerenciar a conta {account_login}.")
    else:
        messages.success(request, f"Permissões de {manager_username} atualizadas para a conta {account_login}.")

    return redirect("server:manage_lineage_accounts")


@conditional_otp_required
@require_lineage_connection
@require_POST
def remove_contra_mestre(request, link_id):
    link = get_object_or_404(ManagedLineageAccount, pk=link_id)
    if not request.user.is_email_master_owner:
        owner = request.user.get_email_master_owner()
        if owner and owner != request.user:
            messages.error(
                request,
                _("Somente a conta mestre %(owner)s pode revogar acessos com este e-mail.") % {"owner": owner.username},
            )
        else:
            messages.error(request, _("Você não tem permissão para revogar acessos."))
        return redirect("server:manage_lineage_accounts")

    is_owner = False
    conta = LineageAccount.get_account_by_login(link.account_login)
    if conta and conta.get("linked_uuid") == str(request.user.uuid):
        is_owner = True

    if not (link.created_by == request.user or is_owner or request.user.is_superuser):
        messages.error(request, "Você não pode remover este contra mestre.")
        return redirect("server:manage_lineage_accounts")

    link.delete()
    messages.success(request, "Contra mestre removido com sucesso.")
    return redirect("server:manage_lineage_accounts")


@conditional_otp_required
@require_lineage_connection
@require_POST
def set_active_lineage_account(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("server:account_dashboard")
    account_login = (request.POST.get("account_login") or "").strip()

    if not account_login:
        messages.error(request, "Selecione uma conta válida.")
        return redirect(next_url)

    try:
        set_active_login(request, account_login)
        messages.success(request, f"Conta {account_login} definida como ativa.")
    except PermissionError:
        messages.error(request, "Você não tem permissão para usar essa conta.")

    return redirect(next_url)


@conditional_otp_required
@require_lineage_connection
@require_POST
def unlink_lineage_account(request):
    """
    Desvincula uma conta do Lineage do UUID do usuário atual.
    Remove o linked_uuid e o email da conta no banco do jogo.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    account_login = (request.POST.get("account_login") or "").strip()
    
    if not account_login:
        messages.error(request, _("Informe o login da conta para desvincular."))
        return redirect("server:manage_lineage_accounts")
    
    # Verifica se o usuário tem acesso a esta conta
    if not user_has_access(request.user, account_login):
        messages.error(request, _("Você não tem permissão para desvincular esta conta."))
        return redirect("server:manage_lineage_accounts")
    
    # Não permite desvincular a conta principal (username)
    if account_login == request.user.username:
        messages.error(request, _("Você não pode desvincular sua conta principal."))
        return redirect("server:manage_lineage_accounts")
    
    try:
        from utils.dynamic_import import get_query_class
        LineageAccount = get_query_class("LineageAccount")
        
        if not LineageAccount or not hasattr(LineageAccount, 'unlink_account_from_user'):
            messages.error(request, _("Funcionalidade de desvinculação não disponível."))
            return redirect("server:manage_lineage_accounts")
        
        user_uuid = str(request.user.uuid) if hasattr(request.user, 'uuid') else None
        if not user_uuid:
            messages.error(request, _("UUID do usuário não encontrado."))
            return redirect("server:manage_lineage_accounts")
        
        logger.info(f"[unlink_lineage_account] Desvinculando conta {account_login} do UUID {user_uuid}")
        
        # Verifica se a conta que está sendo desvinculada é a conta ativa
        active_login = get_active_login(request)
        was_active = (active_login == account_login)
        
        success = LineageAccount.unlink_account_from_user(account_login, user_uuid)
        
        if success:
            # Se a conta desvinculada era a ativa, redefine para a conta principal ANTES de qualquer outra coisa
            if was_active:
                logger.info(f"[unlink_lineage_account] Conta ativa {account_login} foi desvinculada, redefinindo para conta principal")
                set_active_login(request, request.user.username)
                messages.warning(
                    request, 
                    _("Conta %(account)s desvinculada com sucesso. Como ela estava ativa, a conta principal foi definida como ativa.") % {"account": account_login}
                )
            else:
                messages.success(request, _("Conta %(account)s desvinculada com sucesso.") % {"account": account_login})
            
            logger.info(f"[unlink_lineage_account] Conta {account_login} desvinculada com sucesso")
        else:
            messages.error(request, _("Não foi possível desvincular a conta. Verifique se ela está vinculada ao seu usuário."))
            logger.warning(f"[unlink_lineage_account] Falha ao desvincular conta {account_login}")
            
    except Exception as e:
        logger.error(f"[unlink_lineage_account] Erro ao desvincular conta: {e}", exc_info=True)
        messages.error(request, _("Erro ao desvincular a conta: %(error)s") % {"error": str(e)})
    
    return redirect("server:manage_lineage_accounts")
