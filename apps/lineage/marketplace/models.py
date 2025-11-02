from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.main.home.models import User
from core.models import BaseModel
from .choices import (
    TRANSFER_STATUS_CHOICES,
    TRANSACTION_TYPE_CHOICES,
    TRANSACTION_STATUS_CHOICES,
    CURRENCY_CHOICES,
    CLAIM_STATUS_CHOICES
)


class CharacterTransfer(BaseModel):
    """
    Modelo para gerenciar transferências de personagens no marketplace.
    Armazena informações sobre vendas de personagens entre jogadores.
    """
    # IDs do personagem (do banco L2)
    char_id = models.IntegerField(_("ID do Personagem"), db_index=True)
    char_name = models.CharField(_("Nome do Personagem"), max_length=100)
    char_level = models.IntegerField(_("Level do Personagem"))
    char_class = models.IntegerField(_("Classe do Personagem"))
    
    # Contas (do banco L2)
    old_account = models.CharField(_("Conta Antiga"), max_length=100)
    new_account = models.CharField(_("Conta Nova"), max_length=100, blank=True, null=True)
    
    # Usuários (do Django)
    seller = models.ForeignKey(
        User,
        verbose_name=_("Vendedor"),
        on_delete=models.CASCADE,
        related_name='character_sales'
    )
    buyer = models.ForeignKey(
        User,
        verbose_name=_("Comprador"),
        on_delete=models.SET_NULL,
        related_name='character_purchases',
        null=True,
        blank=True
    )
    
    # Valores (sempre em BRL - integrado com sistema de wallet)
    price = models.DecimalField(_("Preço (R$)"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("Moeda"), max_length=10, choices=CURRENCY_CHOICES, default='BRL', editable=False)
    
    # Status e informações
    status = models.CharField(_("Status"), max_length=20, choices=TRANSFER_STATUS_CHOICES, default='pending')
    notes = models.TextField(_("Observações"), blank=True)
    
    # Datas
    listed_at = models.DateTimeField(_("Listado em"), auto_now_add=True)
    sold_at = models.DateTimeField(_("Vendido em"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Transferência de Personagem")
        verbose_name_plural = _("Transferências de Personagens")
        ordering = ['-listed_at']
        indexes = [
            models.Index(fields=['status', '-listed_at']),
            models.Index(fields=['char_id']),
            models.Index(fields=['seller']),
        ]
    
    def __str__(self):
        return f"{self.char_name} (Level {self.char_level}) - {self.get_status_display()}"


class MarketplaceTransaction(BaseModel):
    """
    Modelo para registrar transações financeiras do marketplace.
    """
    transfer = models.ForeignKey(
        CharacterTransfer,
        verbose_name=_("Transferência"),
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(
        _("Tipo de Transação"),
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES
    )
    
    amount = models.DecimalField(_("Valor"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("Moeda"), max_length=10, choices=CURRENCY_CHOICES)
    
    user = models.ForeignKey(
        User,
        verbose_name=_("Usuário"),
        on_delete=models.CASCADE,
        related_name='marketplace_transactions'
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending'
    )
    
    notes = models.TextField(_("Observações"), blank=True)
    
    # Referência externa (ex: ID do pagamento no gateway)
    external_reference = models.CharField(_("Referência Externa"), max_length=255, blank=True)
    
    completed_at = models.DateTimeField(_("Completado em"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Transação do Marketplace")
        verbose_name_plural = _("Transações do Marketplace")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transfer', 'status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency} - {self.user.username}"


class ClaimRequest(BaseModel):
    """
    Modelo para gerenciar reivindicações/disputas de personagens.
    """
    transfer = models.ForeignKey(
        CharacterTransfer,
        verbose_name=_("Transferência"),
        on_delete=models.CASCADE,
        related_name='claims'
    )
    
    char_id = models.IntegerField(_("ID do Personagem"))
    
    requester = models.ForeignKey(
        User,
        verbose_name=_("Solicitante"),
        on_delete=models.CASCADE,
        related_name='claim_requests'
    )
    
    reason = models.TextField(_("Motivo da Reivindicação"))
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=CLAIM_STATUS_CHOICES,
        default='pending'
    )
    
    admin_notes = models.TextField(_("Notas do Administrador"), blank=True)
    
    reviewed_by = models.ForeignKey(
        User,
        verbose_name=_("Revisado por"),
        on_delete=models.SET_NULL,
        related_name='reviewed_claims',
        null=True,
        blank=True
    )
    
    reviewed_at = models.DateTimeField(_("Revisado em"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Reivindicação de Personagem")
        verbose_name_plural = _("Reivindicações de Personagens")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transfer']),
        ]
    
    def __str__(self):
        return f"Claim #{self.id} - {self.transfer.char_name} - {self.get_status_display()}"

