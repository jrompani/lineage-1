"""
Serviço para gerenciar a vinculação automática de contas do Lineage 2 à conta mestre.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import logging

from django.contrib import messages
from django.http import HttpRequest

from apps.main.home.models import EmailOwnership, User
from utils.dynamic_import import get_query_class

logger = logging.getLogger(__name__)


class LineageAccountLinker:
    """
    Classe responsável por vincular automaticamente contas do Lineage 2
    à conta mestre baseada no e-mail.
    """
    
    def __init__(self, user_email: str, master_user: User):
        """
        Inicializa o linker com o e-mail e o usuário mestre.
        
        Args:
            user_email: E-mail para buscar contas do Lineage
            master_user: Usuário que é a conta mestre deste e-mail
        """
        self.user_email = user_email
        self.master_user = master_user
        self.master_uuid = str(master_user.uuid) if hasattr(master_user, 'uuid') else None
        
        # Inicializa classes do Lineage
        self.LineageAccount = get_query_class("LineageAccount")
        self.LineageDBClass = get_query_class("LineageDB")
        self.lineage_db = None
        
        if self.LineageDBClass:
            try:
                self.lineage_db = self.LineageDBClass()
                if not (self.lineage_db and getattr(self.lineage_db, 'enabled', False)):
                    self.lineage_db = None
            except Exception as e:
                logger.warning(f"[LineageAccountLinker] Erro ao inicializar LineageDB: {e}")
                self.lineage_db = None
    
    def find_accounts_by_email(self) -> List[Dict]:
        """
        Busca todas as contas do Lineage com o e-mail especificado.
        Usa SQL direto para evitar problemas de cache.
        
        Returns:
            Lista de dicionários com informações das contas encontradas
        """
        if not self.lineage_db:
            logger.warning("[LineageAccountLinker] LineageDB não disponível")
            return []
        
        try:
            logger.info(f"[LineageAccountLinker] Buscando contas com e-mail: {self.user_email} (SQL direto)")
            sql = """
                SELECT login, linked_uuid, email
                FROM accounts
                WHERE email = :email
            """
            contas = self.lineage_db.select(sql, {"email": self.user_email})
            logger.info(f"[LineageAccountLinker] Contas encontradas: {len(contas) if contas else 0}")
            
            if contas:
                for conta in contas:
                    login = self._extract_field(conta, 'login')
                    linked_uuid = self._extract_field(conta, 'linked_uuid')
                    email = self._extract_field(conta, 'email')
                    logger.info(f"[LineageAccountLinker] Conta: login={login}, linked_uuid={linked_uuid}, email={email}")
            
            return contas or []
        except Exception as e:
            logger.error(f"[LineageAccountLinker] Erro ao buscar contas: {e}", exc_info=True)
            return []
    
    def _extract_field(self, conta, field_name: str) -> Optional[str]:
        """
        Extrai um campo de uma conta, suportando diferentes formatos.
        
        Args:
            conta: Objeto da conta (dict, objeto, etc)
            field_name: Nome do campo a extrair
            
        Returns:
            Valor do campo ou None
        """
        if isinstance(conta, dict):
            return conta.get(field_name)
        elif hasattr(conta, field_name):
            return getattr(conta, field_name, None)
        elif hasattr(conta, '__getitem__'):
            try:
                return conta.get(field_name) if hasattr(conta, 'get') else conta[field_name]
            except (KeyError, TypeError):
                return None
        return None
    
    def _normalize_uuid(self, uuid_value) -> Optional[str]:
        """
        Normaliza um UUID para string, tratando None e strings vazias.
        
        Args:
            uuid_value: Valor do UUID (pode ser None, string, etc)
            
        Returns:
            UUID normalizado como string ou None
        """
        if not uuid_value:
            return None
        
        uuid_str = str(uuid_value).strip()
        return uuid_str if uuid_str else None
    
    def _update_account_email(self, login: str) -> bool:
        """
        Atualiza o e-mail de uma conta do Lineage.
        
        Args:
            login: Login da conta
            
        Returns:
            True se atualizou com sucesso, False caso contrário
        """
        if not self.lineage_db:
            return False
        
        try:
            sql = """
                UPDATE accounts
                SET email = :email
                WHERE login = :login
            """
            params = {
                "email": self.user_email,
                "login": login
            }
            result = self.lineage_db.update(sql, params)
            
            if result and result > 0:
                # Verifica se realmente atualizou
                verify_sql = """
                    SELECT email
                    FROM accounts
                    WHERE login = :login
                    LIMIT 1
                """
                verify_result = self.lineage_db.select(verify_sql, {"login": login})
                if verify_result:
                    verify_email = self._extract_field(verify_result[0], 'email')
                    if verify_email == self.user_email:
                        logger.info(f"[LineageAccountLinker] ✅ Email da conta {login} atualizado com sucesso")
                        return True
                    else:
                        logger.error(f"[LineageAccountLinker] ❌ Email não foi atualizado! Esperado: {self.user_email}, Encontrado: {verify_email}")
                else:
                    logger.warning(f"[LineageAccountLinker] ⚠️ Não foi possível verificar o email após UPDATE")
            else:
                logger.warning(f"[LineageAccountLinker] ⚠️ UPDATE de email não afetou nenhuma linha para conta {login}")
            
            return False
        except Exception as e:
            logger.error(f"[LineageAccountLinker] Erro ao atualizar email da conta {login}: {e}", exc_info=True)
            return False
    
    def _link_account(self, login: str) -> bool:
        """
        Vincula uma conta do Lineage ao UUID da conta mestre.
        
        Args:
            login: Login da conta a vincular
            
        Returns:
            True se vinculou com sucesso, False caso contrário
        """
        if not self.master_uuid:
            logger.warning("[LineageAccountLinker] master_uuid não disponível")
            return False
        
        # Tenta usar link_account_to_user primeiro
        if self.LineageAccount and hasattr(self.LineageAccount, 'link_account_to_user'):
            logger.info(f"[LineageAccountLinker] Tentando vincular {login} via link_account_to_user")
            success = self.LineageAccount.link_account_to_user(login, self.master_uuid)
            
            if success and (not isinstance(success, int) or success > 0):
                logger.info(f"[LineageAccountLinker] ✅ Conta {login} vinculada via link_account_to_user")
                # Atualiza também o email
                self._update_account_email(login)
                return True
            else:
                logger.info(f"[LineageAccountLinker] link_account_to_user retornou {success}, tentando UPDATE direto")
        
        # Se link_account_to_user não funcionou, faz UPDATE direto
        if not self.lineage_db:
            return False
        
        try:
            sql = """
                UPDATE accounts
                SET linked_uuid = :uuid, email = :email
                WHERE login = :login AND (linked_uuid IS NULL OR linked_uuid = '')
            """
            params = {
                "uuid": self.master_uuid,
                "email": self.user_email,
                "login": login
            }
            result = self.lineage_db.update(sql, params)
            
            if result and result > 0:
                logger.info(f"[LineageAccountLinker] ✅ Conta {login} vinculada via UPDATE direto")
                return True
            else:
                logger.warning(f"[LineageAccountLinker] ⚠️ UPDATE não afetou nenhuma linha para conta {login}")
                return False
        except Exception as e:
            logger.error(f"[LineageAccountLinker] Erro ao vincular conta {login}: {e}", exc_info=True)
            return False
    
    def _relink_account(self, login: str, current_uuid: str) -> bool:
        """
        Re-vincula uma conta que está vinculada a outro UUID.
        
        Args:
            login: Login da conta
            current_uuid: UUID atual da conta
            
        Returns:
            True se re-vinculou com sucesso, False caso contrário
        """
        if not self.lineage_db or not self.master_uuid:
            return False
        
        try:
            logger.info(f"[LineageAccountLinker] Re-vinculando conta {login} de {current_uuid} para {self.master_uuid}")
            sql = """
                UPDATE accounts
                SET linked_uuid = :uuid, email = :email
                WHERE login = :login
            """
            params = {
                "uuid": self.master_uuid,
                "email": self.user_email,
                "login": login
            }
            result = self.lineage_db.update(sql, params)
            
            if result and result > 0:
                logger.info(f"[LineageAccountLinker] ✅ Conta {login} re-vinculada com sucesso")
                return True
            else:
                logger.warning(f"[LineageAccountLinker] ⚠️ UPDATE não afetou nenhuma linha para conta {login}")
                return False
        except Exception as e:
            logger.error(f"[LineageAccountLinker] Erro ao re-vincular conta {login}: {e}", exc_info=True)
            return False
    
    def process_account(self, conta: Dict) -> Tuple[str, bool]:
        """
        Processa uma conta individual, decidindo se deve vincular, atualizar ou pular.
        
        Args:
            conta: Dicionário com informações da conta
            
        Returns:
            Tupla (action, success) onde action é 'linked', 'updated', 'skipped' ou 'relinked'
        """
        login = self._extract_field(conta, 'login')
        if not login:
            logger.warning(f"[LineageAccountLinker] Conta sem login: {conta}")
            return ('skipped', False)
        
        current_linked_uuid = self._normalize_uuid(self._extract_field(conta, 'linked_uuid'))
        current_email = self._extract_field(conta, 'email')
        
        logger.info(f"[LineageAccountLinker] Processando conta: {login}, linked_uuid={current_linked_uuid}, master_uuid={self.master_uuid}")
        
        # Se já está vinculada ao UUID correto, apenas atualiza o email
        if current_linked_uuid == self.master_uuid:
            logger.info(f"[LineageAccountLinker] Conta {login} já está vinculada ao UUID correto")
            if self._update_account_email(login):
                # Se o email já estava correto, conta como skipped
                if current_email == self.user_email:
                    return ('skipped', True)
                return ('updated', True)
            return ('skipped', False)
        
        # Se não está vinculada, tenta vincular
        if not current_linked_uuid:
            if self._link_account(login):
                return ('linked', True)
            return ('skipped', False)
        
        # Se está vinculada a outro UUID, re-vincula
        if current_linked_uuid != self.master_uuid:
            if self._relink_account(login, current_linked_uuid):
                return ('relinked', True)
            return ('skipped', False)
        
        return ('skipped', False)
    
    def link_all_accounts(self) -> Dict[str, int]:
        """
        Busca e vincula todas as contas do Lineage com o e-mail especificado.
        
        Returns:
            Dicionário com contadores: linked, updated, relinked, skipped
        """
        if not self.master_uuid:
            logger.warning("[LineageAccountLinker] master_uuid não disponível")
            return {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}
        
        contas = self.find_accounts_by_email()
        if not contas:
            logger.info("[LineageAccountLinker] Nenhuma conta encontrada")
            return {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}
        
        counters = {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}
        
        for conta in contas:
            action, success = self.process_account(conta)
            if success:
                counters[action] = counters.get(action, 0) + 1
        
        logger.info(f"[LineageAccountLinker] Resultado: {counters}")
        return counters
    
    @classmethod
    def link_accounts_for_email(cls, user_email: str, request: Optional[HttpRequest] = None) -> Dict[str, int]:
        """
        Método de conveniência para vincular contas de um e-mail.
        
        Args:
            user_email: E-mail para buscar contas
            request: Request opcional para adicionar mensagens
            
        Returns:
            Dicionário com contadores de ações realizadas
        """
        if not user_email:
            return {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}
        
        try:
            # Verifica se existe uma conta mestre para este e-mail
            email_ownership = EmailOwnership.objects.filter(email=user_email).first()
            if not email_ownership:
                logger.info(f"[LineageAccountLinker] Não existe EmailOwnership para o e-mail {user_email}")
                return {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}
            
            master_user = email_ownership.owner
            linker = cls(user_email, master_user)
            counters = linker.link_all_accounts()
            
            # Adiciona mensagem se houver vinculações novas
            if request and counters.get('linked', 0) > 0:
                messages.info(
                    request,
                    f"✅ {counters['linked']} conta(s) do Lineage foram automaticamente vinculadas à conta mestre {master_user.username}."
                )
            
            return counters
        except Exception as e:
            logger.error(f"[LineageAccountLinker] Erro ao vincular contas: {e}", exc_info=True)
            return {'linked': 0, 'updated': 0, 'relinked': 0, 'skipped': 0}

