from apps.lineage.payment.models import PedidoPagamento, Pagamento
from django.db.models import Sum, Count, Avg
from decimal import Decimal


def pedidos_pagamentos_resumo():
    pedidos = PedidoPagamento.objects.all().order_by('-data_criacao')
    relatorio = []

    # Mapeamento de status do modelo para o template
    status_mapping = {
        'CONFIRMADO': 'aprovado',
        'PENDENTE': 'pendente',
        'FALHOU': 'cancelado',
        'PROCESSANDO': 'processando',
    }

    # Mapeamento de métodos de pagamento
    metodo_mapping = {
        'MercadoPago': 'pix',  # MercadoPago geralmente usa PIX
        'Stripe': 'cartao',    # Stripe geralmente usa cartão
        'PIX': 'pix',
        'CARTAO': 'cartao',
        'BOLETO': 'boleto',
    }

    total_valor_pago = Decimal('0.00')
    total_bonus = Decimal('0.00')
    total_creditado = Decimal('0.00')
    total_moedas = Decimal('0.00')
    contador_status = {'aprovado': 0, 'pendente': 0, 'cancelado': 0, 'processando': 0}

    for pedido in pedidos:
        pagamento = Pagamento.objects.filter(pedido_pagamento=pedido).first()
        
        # Determina o status para exibição
        status_pedido = status_mapping.get(pedido.status, pedido.status.lower())
        
        # Determina o método de pagamento para exibição
        metodo_pagamento = metodo_mapping.get(pedido.metodo, pedido.metodo.lower())
        
        # Calcula percentual de bônus
        percentual_bonus = Decimal('0.00')
        if pedido.valor_pago > 0:
            percentual_bonus = (pedido.bonus_aplicado / pedido.valor_pago) * 100
        
        # Acumula totais
        total_valor_pago += pedido.valor_pago
        total_bonus += pedido.bonus_aplicado
        total_creditado += pedido.total_creditado
        total_moedas += pedido.moedas_geradas
        if status_pedido in contador_status:
            contador_status[status_pedido] += 1
        
        relatorio.append({
            'id_pedido': pedido.id,
            'usuario': pedido.usuario.username,
            'valor': pedido.valor_pago,
            'bonus_aplicado': pedido.bonus_aplicado,
            'total_creditado': pedido.total_creditado,
            'moedas_geradas': pedido.moedas_geradas,
            'percentual_bonus': percentual_bonus,
            'status': status_pedido,
            'metodo_pagamento': metodo_pagamento,
            'data': pedido.data_criacao,
        })

    # Calcula resumo geral
    total_pedidos = len(relatorio)
    media_valor = total_valor_pago / total_pedidos if total_pedidos > 0 else Decimal('0.00')
    media_bonus = total_bonus / total_pedidos if total_pedidos > 0 else Decimal('0.00')
    percentual_bonus_geral = (total_bonus / total_valor_pago * 100) if total_valor_pago > 0 else Decimal('0.00')
    
    resumo = {
        'total_pedidos': total_pedidos,
        'total_valor_pago': total_valor_pago,
        'total_bonus': total_bonus,
        'total_creditado': total_creditado,
        'total_moedas': total_moedas,
        'media_valor': media_valor,
        'media_bonus': media_bonus,
        'percentual_bonus_geral': percentual_bonus_geral,
        'status_contador': contador_status,
    }

    return {
        'relatorio': relatorio,
        'resumo': resumo
    }
