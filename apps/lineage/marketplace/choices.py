from django.utils.translation import gettext_lazy as _


TRANSFER_STATUS_CHOICES = [
    ('pending', _('Pendente')),
    ('for_sale', _('À Venda')),
    ('sold', _('Vendido')),
    ('cancelled', _('Cancelado')),
    ('disputed', _('Em Disputa')),
]

TRANSACTION_TYPE_CHOICES = [
    ('sale', _('Venda')),
    ('purchase', _('Compra')),
    ('refund', _('Reembolso')),
    ('commission', _('Comissão')),
]

TRANSACTION_STATUS_CHOICES = [
    ('pending', _('Pendente')),
    ('completed', _('Completado')),
    ('failed', _('Falhou')),
    ('cancelled', _('Cancelado')),
]

CURRENCY_CHOICES = [
    ('BRL', _('Real (R$)')),
]

CLAIM_STATUS_CHOICES = [
    ('pending', _('Pendente')),
    ('under_review', _('Em Análise')),
    ('approved', _('Aprovado')),
    ('rejected', _('Rejeitado')),
]

