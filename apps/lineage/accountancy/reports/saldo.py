from apps.lineage.wallet.models import Wallet, TransacaoWallet
from django.db.models import Sum, Count, Max, Min
from decimal import Decimal


def saldo_usuario(usuario):
    try:
        wallet = Wallet.objects.get(usuario=usuario)
        saldo_wallet = wallet.saldo
        saldo_bonus = wallet.saldo_bonus
        data_criacao = wallet.created_at
    except Wallet.DoesNotExist:
        return {
            'saldo_wallet': 0,
            'saldo_bonus': 0,
            'saldo_total': 0,
            'saldo_calculado': 0,
            'diferenca': 0,
            'percentual_diferenca': 0,
            'num_transacoes': 0,
            'num_entradas': 0,
            'num_saidas': 0,
            'total_entradas': 0,
            'total_saidas': 0,
            'ultima_transacao': None,
            'primeira_transacao': None,
            'data_criacao': None,
            'status': 'sem_carteira'
        }

    # Calcula totais de transações
    entradas = TransacaoWallet.objects.filter(
        wallet=wallet, tipo='ENTRADA'
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    saidas = TransacaoWallet.objects.filter(
        wallet=wallet, tipo='SAIDA'
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    # Conta número de transações e pega a última e primeira
    transacoes_info = TransacaoWallet.objects.filter(wallet=wallet).aggregate(
        total=Count('id'),
        ultima=Max('data'),
        primeira=Min('data')
    )
    
    num_entradas = TransacaoWallet.objects.filter(wallet=wallet, tipo='ENTRADA').count()
    num_saidas = TransacaoWallet.objects.filter(wallet=wallet, tipo='SAIDA').count()

    saldo_calculado = entradas - saidas
    saldo_total = saldo_wallet + saldo_bonus
    diferenca = saldo_wallet - saldo_calculado
    
    # Calcula percentual de diferença
    if saldo_calculado > 0:
        percentual_diferenca = (diferenca / saldo_calculado) * 100
    else:
        percentual_diferenca = Decimal('0.00') if diferenca == 0 else Decimal('100.00')
    
    # Determina o status baseado na diferença
    if diferenca == 0:
        status = 'consistente'
    elif abs(diferenca) <= 0.01:  # Tolerância de 1 centavo
        status = 'consistente'
    elif abs(diferenca) <= 1.00:  # Tolerância de 1 real
        status = 'pequena_discrepancia'
    else:
        status = 'discrepancia'

    return {
        'saldo_wallet': saldo_wallet,
        'saldo_bonus': saldo_bonus,
        'saldo_total': saldo_total,
        'saldo_calculado': saldo_calculado,
        'diferenca': diferenca,
        'percentual_diferenca': percentual_diferenca,
        'num_transacoes': transacoes_info['total'],
        'num_entradas': num_entradas,
        'num_saidas': num_saidas,
        'total_entradas': entradas,
        'total_saidas': saidas,
        'ultima_transacao': transacoes_info['ultima'],
        'primeira_transacao': transacoes_info['primeira'],
        'data_criacao': data_criacao,
        'status': status
    }
