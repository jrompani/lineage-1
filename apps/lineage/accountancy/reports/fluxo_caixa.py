from apps.lineage.wallet.models import TransacaoWallet
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from decimal import Decimal

def fluxo_caixa_por_dia():
    # Renomeando a anotação para evitar conflito com o campo 'data'
    transacoes = TransacaoWallet.objects.annotate(data_truncada=TruncDate('data'))

    entradas = transacoes.filter(tipo='ENTRADA').values('data_truncada').annotate(
        total=Sum('valor'),
        quantidade=Count('id')
    ).order_by('-data_truncada')

    saidas = transacoes.filter(tipo='SAIDA').values('data_truncada').annotate(
        total=Sum('valor'),
        quantidade=Count('id')
    ).order_by('-data_truncada')

    # Junta os dados por data
    dias = {}
    for entrada in entradas:
        dias[entrada['data_truncada']] = {
            'entrada': entrada['total'],
            'saida': Decimal('0.00'),
            'num_entradas': entrada['quantidade'],
            'num_saidas': 0
        }

    for saida in saidas:
        if saida['data_truncada'] in dias:
            dias[saida['data_truncada']]['saida'] = saida['total']
            dias[saida['data_truncada']]['num_saidas'] = saida['quantidade']
        else:
            dias[saida['data_truncada']] = {
                'entrada': Decimal('0.00'),
                'saida': saida['total'],
                'num_entradas': 0,
                'num_saidas': saida['quantidade']
            }

    # Converte pra lista ordenada por data decrescente e calcula saldo acumulado
    relatorio = []
    saldo_acumulado = Decimal('0.00')
    total_entradas_geral = Decimal('0.00')
    total_saidas_geral = Decimal('0.00')
    
    for data, valores in sorted(dias.items(), reverse=True):
        saldo = valores['entrada'] - valores['saida']
        saldo_acumulado += saldo
        total_entradas_geral += valores['entrada']
        total_saidas_geral += valores['saida']
        
        num_transacoes = valores['num_entradas'] + valores['num_saidas']
        
        # Calcula percentual de variação (comparando com o dia anterior)
        percentual_variacao = Decimal('0.00')
        if len(relatorio) > 0:
            saldo_anterior = relatorio[-1]['saldo']
            if saldo_anterior != 0:
                percentual_variacao = ((saldo - saldo_anterior) / abs(saldo_anterior)) * 100
        
        # Determina a tendência baseada no saldo
        if saldo > 0:
            tendencia = 'positiva'
        elif saldo < 0:
            tendencia = 'negativa'
        else:
            tendencia = 'estavel'
        
        relatorio.append({
            'data': data,
            'entradas': valores['entrada'],
            'saidas': valores['saida'],
            'saldo': saldo,
            'saldo_acumulado': saldo_acumulado,
            'num_transacoes': num_transacoes,
            'num_entradas': valores['num_entradas'],
            'num_saidas': valores['num_saidas'],
            'percentual_variacao': percentual_variacao,
            'tendencia': tendencia
        })

    # Adiciona resumo geral
    taxa_entrada_saida = Decimal('0.00')
    if total_saidas_geral > 0:
        taxa_entrada_saida = total_entradas_geral / total_saidas_geral
    
    resumo = {
        'total_entradas': total_entradas_geral,
        'total_saidas': total_saidas_geral,
        'saldo_final': saldo_acumulado,
        'total_dias': len(relatorio),
        'media_entradas': total_entradas_geral / len(relatorio) if len(relatorio) > 0 else Decimal('0.00'),
        'media_saidas': total_saidas_geral / len(relatorio) if len(relatorio) > 0 else Decimal('0.00'),
        'taxa_entrada_saida': taxa_entrada_saida,
    }

    return {
        'relatorio': relatorio,
        'resumo': resumo
    }
