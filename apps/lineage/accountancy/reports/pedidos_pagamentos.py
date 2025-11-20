from apps.lineage.payment.models import PedidoPagamento, Pagamento
from django.db.models import Sum, Count
from decimal import Decimal


def pedidos_pagamentos_resumo(pedidos=None):
    # Se não foi passado um queryset, busca todos os pedidos
    if pedidos is None:
        pedidos = PedidoPagamento.objects.all().select_related('usuario').order_by('-data_criacao')

    # FILTRO IMPORTANTE: Para cálculos financeiros, consideramos apenas pedidos CONFIRMADOS/CONCLUÍDOS
    # Isso garante que os totais representem apenas faturamento real
    # CONCLUÍDO é usado no fluxo do Mercado Pago e é equivalente a CONFIRMADO
    # Aplica o filtro sobre o queryset passado (que pode já estar filtrado)
    pedidos_confirmados = pedidos.filter(status__in=['CONFIRMADO', 'CONCLUÍDO', 'CONCLUIDO'])

    # Mapeamento de status do modelo para o template
    # CONCLUÍDO é usado no fluxo do Mercado Pago e é equivalente a CONFIRMADO
    status_mapping = {
        'CONFIRMADO': 'aprovado',
        'CONCLUÍDO': 'aprovado',  # Status usado no fluxo do Mercado Pago
        'CONCLUIDO': 'aprovado',   # Variação sem acento (por segurança)
        'PENDENTE': 'pendente',
        'FALHOU': 'cancelado',
        'PROCESSANDO': 'processando',
    }

    # Mapeamento de métodos de pagamento para exibição
    # Não assumimos qual método específico foi usado (PIX, cartão, boleto)
    # Apenas formatamos o nome para exibição amigável
    metodo_mapping = {
        'MercadoPago': 'Mercado Pago',
        'Stripe': 'Stripe',
        'PIX': 'PIX',
        'CARTAO': 'Cartão',
        'BOLETO': 'Boleto',
    }

    # Calcula contadores de status para TODOS os pedidos (sem filtros)
    # IMPORTANTE: Sempre conta todos os pedidos, independente dos filtros aplicados
    # Isso permite ver o resumo geral mesmo quando há filtros aplicados
    todos_pedidos = PedidoPagamento.objects.all()
    contador_status_raw = todos_pedidos.values('status').annotate(count=Count('id'))
    contador_status = {'aprovado': 0, 'pendente': 0, 'cancelado': 0, 'processando': 0, 'outros': 0}
    
    # Mapeia os status conhecidos e agrupa os desconhecidos em "outros"
    for item in contador_status_raw:
        status_original = item['status']
        status_mapeado = status_mapping.get(status_original)
        
        if status_mapeado:
            # Status conhecido, adiciona ao contador
            if status_mapeado in contador_status:
                contador_status[status_mapeado] += item['count']
        else:
            # Status desconhecido, adiciona a "outros"
            contador_status['outros'] += item['count']

    # Calcula totais financeiros APENAS de pedidos CONFIRMADOS
    # Usando aggregate para eficiência e precisão
    totais_confirmados = pedidos_confirmados.aggregate(
        total_valor_pago=Sum('valor_pago'),
        total_bonus=Sum('bonus_aplicado'),
        total_moedas=Sum('moedas_geradas'),
        count=Count('id')
    )

    # Valores financeiros (apenas confirmados)
    total_valor_pago = totais_confirmados['total_valor_pago'] or Decimal('0.00')
    total_bonus = totais_confirmados['total_bonus'] or Decimal('0.00')
    # IMPORTANTE: Total creditado deve ser sempre = valor_pago + bonus_aplicado
    # Não somamos o campo total_creditado do banco porque pode estar inconsistente
    # Calculamos dinamicamente para garantir precisão financeira
    total_creditado = total_valor_pago + total_bonus
    total_moedas = totais_confirmados['total_moedas'] or Decimal('0.00')
    total_pedidos_confirmados = totais_confirmados['count'] or 0

    # Não precisamos calcular percentuais aqui - será feito na view apenas para a página atual

    # Calcula resumo geral
    # IMPORTANTE: Os totais financeiros são calculados apenas com pedidos CONFIRMADOS
    # Mas o total de pedidos deve mostrar TODOS os pedidos do sistema (independente de status)
    todos_pedidos_count = todos_pedidos.count()  # Total de pedidos no sistema (todos os status)
    media_valor = total_valor_pago / total_pedidos_confirmados if total_pedidos_confirmados > 0 else Decimal('0.00')
    percentual_bonus_geral = (total_bonus / total_valor_pago * 100) if total_valor_pago > 0 else Decimal('0.00')
    
    resumo = {
        'total_pedidos': todos_pedidos_count,  # Total de TODOS os pedidos (independente de status)
        'total_valor_pago': total_valor_pago,  # Soma apenas de pedidos confirmados
        'total_bonus': total_bonus,  # Soma apenas de pedidos confirmados
        'total_creditado': total_creditado,  # Soma apenas de pedidos confirmados
        'total_moedas': total_moedas,  # Soma apenas de pedidos confirmados
        'media_valor': media_valor,  # Média calculada apenas com pedidos confirmados
        'percentual_bonus_geral': percentual_bonus_geral,  # Percentual calculado apenas com pedidos confirmados
        'status_contador': contador_status,  # Contador de todos os status (mostra aprovados, pendentes, etc)
    }

    return {
        'queryset': pedidos,  # Retorna o queryset para paginação
        'resumo': resumo,
        'status_mapping': status_mapping,
        'metodo_mapping': metodo_mapping,
    }
