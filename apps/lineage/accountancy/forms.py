from django import forms
from django.utils.translation import gettext_lazy as _
from apps.lineage.payment.models import PedidoPagamento
from apps.main.home.models import User


class PedidosPagamentosFilterForm(forms.Form):
    """Formulário para filtros do relatório de pedidos e pagamentos"""
    
    # Status do pedido
    status = forms.ChoiceField(
        choices=[
            ('', _('Todos os status')),
            ('CONFIRMADO', _('Aprovado')),
            ('PENDENTE', _('Pendente')),
            ('FALHOU', _('Cancelado')),
            ('PROCESSANDO', _('Processando')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Status')
    )
    
    # Método de pagamento
    metodo = forms.ChoiceField(
        choices=[
            ('', _('Todos os métodos')),
            ('MercadoPago', 'MercadoPago'),
            ('Stripe', 'Stripe'),
            ('PIX', 'PIX'),
            ('CARTAO', _('Cartão')),
            ('BOLETO', _('Boleto')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Método de Pagamento')
    )
    
    # Período de datas
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label=_('Data Inicial')
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label=_('Data Final')
    )
    
    # Busca por usuário
    usuario = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Buscar por usuário...'),
        }),
        label=_('Usuário')
    )
    
    # Filtro por valor (opcional)
    valor_minimo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
        }),
        label=_('Valor Mínimo (R$)')
    )
    
    valor_maximo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '999999.99',
            'step': '0.01',
        }),
        label=_('Valor Máximo (R$)')
    )


class SaldoUsuariosFilterForm(forms.Form):
    """Formulário para filtros do relatório de saldo de usuários"""
    
    # Busca por usuário
    usuario = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Buscar por usuário...'),
        }),
        label=_('Usuário')
    )
    
    # Filtro por status
    status = forms.ChoiceField(
        choices=[
            ('', _('Todos os status')),
            ('consistente', _('Consistente')),
            ('pequena_discrepancia', _('Pequena Discrepância')),
            ('discrepancia', _('Discrepância')),
            ('sem_carteira', _('Sem Carteira')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Status')
    )
    
    # Filtro por saldo mínimo/máximo
    saldo_minimo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
        }),
        label=_('Saldo Mínimo (R$)')
    )
    
    saldo_maximo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '999999.99',
            'step': '0.01',
        }),
        label=_('Saldo Máximo (R$)')
    )


class FluxoCaixaFilterForm(forms.Form):
    """Formulário para filtros do relatório de fluxo de caixa"""
    
    # Período de datas
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label=_('Data Inicial')
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label=_('Data Final')
    )


class ReconciliacaoWalletFilterForm(forms.Form):
    """Formulário para filtros do relatório de reconciliação de carteiras"""
    
    # Busca por usuário
    usuario = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Buscar por usuário...'),
        }),
        label=_('Usuário')
    )
    
    # Filtro por status
    status = forms.ChoiceField(
        choices=[
            ('', _('Todos os status')),
            ('reconciliado', _('Reconciliado')),
            ('em_analise', _('Em Análise')),
            ('discrepancia', _('Discrepância')),
            ('pendente', _('Pendente')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Status')
    )
    
    # Filtro por diferença mínima/máxima
    diferenca_minima = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '-999999.99',
            'step': '0.01',
        }),
        label=_('Diferença Mínima (R$)')
    )
    
    diferenca_maxima = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '999999.99',
            'step': '0.01',
        }),
        label=_('Diferença Máxima (R$)')
    )
