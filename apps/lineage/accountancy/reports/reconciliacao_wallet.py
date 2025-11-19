from apps.lineage.wallet.models import Wallet, TransacaoWallet
from django.db.models import Sum, Count, Max, Min
from django.utils import timezone
from decimal import Decimal


def reconciliacao_wallet_transacoes():
    wallets = Wallet.objects.all()
    relatorio = []

    total_saldo_wallet = Decimal('0.00')
    total_saldo_banco = Decimal('0.00')
    total_diferenca = Decimal('0.00')
    contador_status = {'reconciliado': 0, 'discrepancia': 0, 'em_analise': 0, 'pendente': 0}

    for wallet in wallets:
        # Calcula totais de transações
        total_entradas = TransacaoWallet.objects.filter(wallet=wallet, tipo='ENTRADA').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        total_saidas = TransacaoWallet.objects.filter(wallet=wallet, tipo='SAIDA').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Conta número de transações e pega datas
        transacoes_info = TransacaoWallet.objects.filter(wallet=wallet).aggregate(
            total=Count('id'),
            ultima=Max('data'),
            primeira=Min('data')
        )
        
        num_entradas = TransacaoWallet.objects.filter(wallet=wallet, tipo='ENTRADA').count()
        num_saidas = TransacaoWallet.objects.filter(wallet=wallet, tipo='SAIDA').count()

        saldo_calculado = total_entradas - total_saidas
        diferenca = wallet.saldo - saldo_calculado
        
        # Calcula percentual de diferença
        if saldo_calculado > 0:
            percentual_diferenca = (diferenca / saldo_calculado) * 100
        else:
            percentual_diferenca = Decimal('0.00') if diferenca == 0 else Decimal('100.00')
        
        # Determina o status baseado na diferença
        if diferenca == 0:
            status = 'reconciliado'
        elif abs(diferenca) <= 0.01:  # Tolerância de 1 centavo
            status = 'reconciliado'
        elif abs(diferenca) <= 1.00:  # Tolerância de 1 real
            status = 'em_analise'
        else:
            status = 'discrepancia'
        
        # Acumula totais
        total_saldo_wallet += wallet.saldo
        total_saldo_banco += saldo_calculado
        total_diferenca += diferenca
        if status in contador_status:
            contador_status[status] += 1

        relatorio.append({
            'usuario': wallet.usuario.username,
            'saldo_wallet': wallet.saldo,
            'saldo_bonus': wallet.saldo_bonus,
            'saldo_total': wallet.saldo + wallet.saldo_bonus,
            'saldo_banco': saldo_calculado,
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'diferenca': diferenca,
            'percentual_diferenca': percentual_diferenca,
            'status': status,
            'num_transacoes': transacoes_info['total'],
            'num_entradas': num_entradas,
            'num_saidas': num_saidas,
            'ultima_transacao': transacoes_info['ultima'],
            'primeira_transacao': transacoes_info['primeira'],
            'ultima_verificacao': timezone.now(),
            'data_criacao': wallet.created_at,
        })

    # Calcula resumo geral
    total_carteiras = len(relatorio)
    percentual_diferenca_geral = (total_diferenca / total_saldo_banco * 100) if total_saldo_banco > 0 else Decimal('0.00')
    
    resumo = {
        'total_carteiras': total_carteiras,
        'total_saldo_wallet': total_saldo_wallet,
        'total_saldo_banco': total_saldo_banco,
        'total_diferenca': total_diferenca,
        'percentual_diferenca_geral': percentual_diferenca_geral,
        'status_contador': contador_status,
    }

    return {
        'relatorio': relatorio,
        'resumo': resumo
    }
