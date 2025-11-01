from datetime import timedelta
from django.utils.timezone import now
from .models import *
from django.db import transaction
from apps.lineage.wallet.signals import aplicar_transacao
from django.utils import timezone

def reconciliar_pendentes_mercadopago(cutoff_minutes: int = 5) -> int:
    """Reconciliador idempotente para pagamentos pendentes do Mercado Pago.

    Busca pagamentos em status 'pending' com pedido PENDENTE criados há pelo menos
    cutoff_minutes e consulta o Mercado Pago por external_reference. Se aprovado,
    aplica bônus/total e conclui o pedido, marcando processado_em.

    Retorna a quantidade reconciliada.
    """
    try:
        import mercadopago
        from decimal import Decimal
        from apps.lineage.wallet.utils import aplicar_compra_com_bonus
    except Exception:
        return 0

    limite = now() - timedelta(minutes=cutoff_minutes)
    pendentes = (
        Pagamento.objects
        .select_related('pedido_pagamento', 'usuario')
        .filter(status='pending', pedido_pagamento__status='PENDENTE', data_criacao__lte=limite)
    )

    if not pendentes.exists():
        return 0

    from django.conf import settings
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    reconciliados = 0

    for pagamento in pendentes:
        pedido = pagamento.pedido_pagamento
        if not pedido or pedido.metodo != 'MercadoPago':
            continue
        try:
            search = sdk.merchant_order().search({'external_reference': str(pagamento.id)})
            if search.get('status') != 200:
                continue
            results = (search.get('response') or {}).get('elements', [])
            for order in results:
                pagamentos_mp = order.get('payments', [])
                aprovado = any(p.get('status') == 'approved' for p in pagamentos_mp)
                if not aprovado:
                    continue
                with transaction.atomic():
                    from apps.lineage.wallet.models import Wallet
                    wallet, _ = Wallet.objects.get_or_create(usuario=pagamento.usuario)
                    valor_total, valor_bonus, _ = aplicar_compra_com_bonus(
                        wallet, Decimal(str(pagamento.valor)), 'MercadoPago'
                    )
                    pagamento.status = 'paid'
                    pagamento.processado_em = timezone.now()
                    pagamento.save()
                    pedido.bonus_aplicado = valor_bonus
                    pedido.total_creditado = valor_total
                    pedido.status = 'CONCLUÍDO'
                    pedido.save()
                    reconciliados += 1
                break
        except Exception:
            continue

    return reconciliados


def expirar_pedidos_antigos():
    limite = now() - timedelta(hours=48)
    PedidoPagamento.objects.filter(status='PENDENTE', data_criacao__lt=limite).update(status='EXPIRADO')


def processar_pedidos_aprovados() -> int:
    processed = 0
    pagamentos = Pagamento.objects.filter(status='approved', pedido_pagamento__status='PENDENTE')
    for pagamento in pagamentos:
        try:
            with transaction.atomic():
                wallet, created = Wallet.objects.get_or_create(usuario=pagamento.usuario)
                aplicar_transacao(
                    wallet=wallet,
                    tipo="ENTRADA",
                    valor=pagamento.valor,
                    descricao="Crédito via MercadoPago (celery beats)",
                    origem="MercadoPago",
                    destino=pagamento.usuario.username
                )
                pagamento.status = "paid"
                pagamento.save()

                pedido = pagamento.pedido_pagamento
                pedido.status = 'CONCLUÍDO'
                pedido.save()
                processed += 1
        except Exception as e:
            # Logar ou tratar o erro de alguma forma
            print(f"Erro ao creditar pagamento {pagamento.id}: {e}")
    return processed
