from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from apps.main.home.models import User
import json

from .reports.saldo import saldo_usuario
from .reports.fluxo_caixa import fluxo_caixa_por_dia
from .reports.pedidos_pagamentos import pedidos_pagamentos_resumo
from .reports.reconciliacao_wallet import reconciliacao_wallet_transacoes


@staff_member_required
def relatorio_saldo_usuarios(request):
    usuarios = User.objects.all()
    relatorio = []
    
    total_saldo_wallet = 0
    total_saldo_bonus = 0
    total_saldo_calculado = 0
    total_diferenca = 0
    total_transacoes = 0
    contador_status = {'consistente': 0, 'pequena_discrepancia': 0, 'discrepancia': 0, 'sem_carteira': 0}

    for usuario in usuarios:
        info = saldo_usuario(usuario)
        relatorio.append({
            'usuario': usuario.username,
            **info
        })
        
        # Acumula totais
        total_saldo_wallet += float(info.get('saldo_wallet', 0))
        total_saldo_bonus += float(info.get('saldo_bonus', 0))
        total_saldo_calculado += float(info.get('saldo_calculado', 0))
        total_diferenca += float(info.get('diferenca', 0))
        total_transacoes += info.get('num_transacoes', 0)
        status = info.get('status', 'sem_carteira')
        if status in contador_status:
            contador_status[status] += 1

    resumo = {
        'total_usuarios': len(relatorio),
        'total_saldo_wallet': total_saldo_wallet,
        'total_saldo_bonus': total_saldo_bonus,
        'total_saldo_total': total_saldo_wallet + total_saldo_bonus,
        'total_saldo_calculado': total_saldo_calculado,
        'total_diferenca': total_diferenca,
        'total_transacoes': total_transacoes,
        'status_contador': contador_status,
    }

    return render(request, 'accountancy/relatorio_saldo.html', {
        'relatorio': relatorio,
        'resumo': resumo
    })


@staff_member_required
def relatorio_fluxo_caixa(request):
    dados = fluxo_caixa_por_dia()
    relatorio = dados['relatorio']
    resumo = dados['resumo']

    labels = [str(item['data'].strftime('%d/%m')) for item in relatorio]
    entradas = [float(item['entradas']) for item in relatorio]
    saidas = [float(item['saidas']) for item in relatorio]
    saldos = [float(item['saldo']) for item in relatorio]

    labels.reverse()
    entradas.reverse()
    saidas.reverse()
    saldos.reverse()

    context = {
        'labels': json.dumps(labels),
        'entradas': json.dumps(entradas),
        'saidas': json.dumps(saidas),
        'saldos': json.dumps(saldos),
        'relatorio': relatorio,
        'resumo': resumo,
    }

    return render(request, 'accountancy/relatorio_fluxo_caixa.html', context)


@staff_member_required
def relatorio_pedidos_pagamentos(request):
    dados = pedidos_pagamentos_resumo()
    return render(request, 'accountancy/relatorio_pedidos_pagamentos.html', {
        'relatorio': dados['relatorio'],
        'resumo': dados['resumo']
    })


@staff_member_required
def relatorio_reconciliacao_wallet(request):
    dados = reconciliacao_wallet_transacoes()
    return render(request, 'accountancy/relatorio_reconciliacao_wallet.html', {
        'relatorio': dados['relatorio'],
        'resumo': dados['resumo']
    })


@staff_member_required
def dashboard_accountancy(request):
    return render(request, 'accountancy/dashboard.html')
