from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from apps.main.home.models import User
import json

from .forms import (
    PedidosPagamentosFilterForm,
    SaldoUsuariosFilterForm,
    FluxoCaixaFilterForm,
    ReconciliacaoWalletFilterForm,
)
from .reports.saldo import saldo_usuario
from .reports.fluxo_caixa import fluxo_caixa_por_dia
from .reports.pedidos_pagamentos import pedidos_pagamentos_resumo
from .reports.reconciliacao_wallet import reconciliacao_wallet_transacoes


@staff_member_required
def relatorio_saldo_usuarios(request):
    # Inicializa o formulário de filtros
    filter_form = SaldoUsuariosFilterForm(request.GET)
    
    # Obtém todos os usuários
    usuarios = User.objects.all()
    
    # Aplica filtro de usuário (busca por username) se existir
    usuario_filter = None
    if filter_form.is_valid():
        usuario_filter = filter_form.cleaned_data.get('usuario')
        if usuario_filter:
            usuarios = usuarios.filter(username__icontains=usuario_filter)
    
    # Processa TODOS os usuários para calcular totais e contadores
    # Mas filtra por status e saldo
    relatorio_completo = []
    total_saldo_wallet = 0
    total_saldo_bonus = 0
    total_saldo_calculado = 0
    total_diferenca = 0
    total_transacoes = 0
    
    status_filter = None
    saldo_minimo = None
    saldo_maximo = None
    if filter_form.is_valid():
        status_filter = filter_form.cleaned_data.get('status')
        saldo_minimo = filter_form.cleaned_data.get('saldo_minimo')
        saldo_maximo = filter_form.cleaned_data.get('saldo_maximo')

    for usuario in usuarios:
        info = saldo_usuario(usuario)
        
        # Aplica filtros de status e saldo após calcular
        if status_filter and info.get('status') != status_filter:
            continue
        
        saldo_total_usuario = info.get('saldo_wallet', 0) + info.get('saldo_bonus', 0)
        if saldo_minimo is not None and saldo_total_usuario < saldo_minimo:
            continue
        if saldo_maximo is not None and saldo_total_usuario > saldo_maximo:
            continue
        
        relatorio_completo.append({
            'usuario': usuario.username,
            **info
        })
        
        # Acumula totais (apenas usuários filtrados que passaram nos filtros)
        total_saldo_wallet += float(info.get('saldo_wallet', 0))
        total_saldo_bonus += float(info.get('saldo_bonus', 0))
        total_saldo_calculado += float(info.get('saldo_calculado', 0))
        total_diferenca += float(info.get('diferenca', 0))
        total_transacoes += info.get('num_transacoes', 0)

    # Calcula contadores de status para TODOS os usuários (sem filtros)
    todos_usuarios = User.objects.all()
    todos_contadores = {'consistente': 0, 'pequena_discrepancia': 0, 'discrepancia': 0, 'sem_carteira': 0}
    for usuario_geral in todos_usuarios:
        info_geral = saldo_usuario(usuario_geral)
        status_geral = info_geral.get('status', 'sem_carteira')
        if status_geral in todos_contadores:
            todos_contadores[status_geral] += 1

    resumo = {
        'total_usuarios': len(relatorio_completo),  # Usuários filtrados
        'total_saldo_wallet': total_saldo_wallet,
        'total_saldo_bonus': total_saldo_bonus,
        'total_saldo_total': total_saldo_wallet + total_saldo_bonus,
        'total_saldo_calculado': total_saldo_calculado,
        'total_diferenca': total_diferenca,
        'total_transacoes': total_transacoes,
        'status_contador': todos_contadores,  # Contadores de todos os usuários
    }
    
    # Paginação
    paginator = Paginator(relatorio_completo, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accountancy/relatorio_saldo.html', {
        'relatorio': list(page_obj),
        'resumo': resumo,
        'page_obj': page_obj,
        'filter_form': filter_form,
    })


@staff_member_required
def relatorio_fluxo_caixa(request):
    # Inicializa o formulário de filtros
    filter_form = FluxoCaixaFilterForm(request.GET)
    
    # Obtém dados do fluxo de caixa
    dados = fluxo_caixa_por_dia()
    relatorio = dados['relatorio']
    resumo = dados['resumo']
    
    # Aplica filtros de data se o formulário for válido
    if filter_form.is_valid():
        data_inicio = filter_form.cleaned_data.get('data_inicio')
        data_fim = filter_form.cleaned_data.get('data_fim')
        
        if data_inicio:
            relatorio = [item for item in relatorio if item['data'] >= data_inicio]
        if data_fim:
            relatorio = [item for item in relatorio if item['data'] <= data_fim]

    labels = [str(item['data'].strftime('%d/%m')) for item in relatorio]
    entradas = [float(item['entradas']) for item in relatorio]
    saidas = [float(item['saidas']) for item in relatorio]
    saldos = [float(item['saldo']) for item in relatorio]

    labels.reverse()
    entradas.reverse()
    saidas.reverse()
    saldos.reverse()

    # Paginação
    paginator = Paginator(relatorio, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'labels': json.dumps(labels),
        'entradas': json.dumps(entradas),
        'saidas': json.dumps(saidas),
        'saldos': json.dumps(saldos),
        'relatorio': list(page_obj),
        'resumo': resumo,
        'page_obj': page_obj,
        'filter_form': filter_form,
    }

    return render(request, 'accountancy/relatorio_fluxo_caixa.html', context)


@staff_member_required
def relatorio_pedidos_pagamentos(request):
    # Inicializa o formulário de filtros
    filter_form = PedidosPagamentosFilterForm(request.GET)
    
    # Obtém o queryset base
    from apps.lineage.payment.models import PedidoPagamento
    pedidos = PedidoPagamento.objects.all().select_related('usuario').order_by('-data_criacao')
    
    # Aplica os filtros se o formulário for válido
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        metodo = filter_form.cleaned_data.get('metodo')
        data_inicio = filter_form.cleaned_data.get('data_inicio')
        data_fim = filter_form.cleaned_data.get('data_fim')
        usuario = filter_form.cleaned_data.get('usuario')
        valor_minimo = filter_form.cleaned_data.get('valor_minimo')
        valor_maximo = filter_form.cleaned_data.get('valor_maximo')
        
        # Aplica filtro de status
        if status:
            pedidos = pedidos.filter(status=status)
        
        # Aplica filtro de método de pagamento
        if metodo:
            pedidos = pedidos.filter(metodo=metodo)
        
        # Aplica filtro de período de datas
        if data_inicio:
            pedidos = pedidos.filter(data_criacao__date__gte=data_inicio)
        if data_fim:
            pedidos = pedidos.filter(data_criacao__date__lte=data_fim)
        
        # Aplica filtro de usuário (busca por username)
        if usuario:
            pedidos = pedidos.filter(usuario__username__icontains=usuario)
        
        # Aplica filtro de valor
        if valor_minimo is not None:
            pedidos = pedidos.filter(valor_pago__gte=valor_minimo)
        if valor_maximo is not None:
            pedidos = pedidos.filter(valor_pago__lte=valor_maximo)
    
    # Obtém o resumo com totais (calculados sobre os pedidos FILTRADOS)
    dados = pedidos_pagamentos_resumo(pedidos=pedidos)
    resumo = dados['resumo']
    
    # Obtém o queryset paginado (apenas para exibição na tabela)
    pedidos_paginados = dados['queryset']
    
    # Configura a paginação - 50 itens por página
    paginator = Paginator(pedidos_paginados, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Processa apenas os pedidos da página atual para o relatório
    relatorio = []
    from decimal import Decimal
    for pedido in page_obj:
        # Calcula percentual de bônus apenas para os pedidos da página atual
        percentual_bonus = Decimal('0.00')
        if pedido.valor_pago > 0:
            percentual_bonus = (pedido.bonus_aplicado / pedido.valor_pago) * 100
        
        relatorio.append({
            'id_pedido': pedido.id,
            'usuario': pedido.usuario.username,
            'valor': pedido.valor_pago,
            'bonus_aplicado': pedido.bonus_aplicado,
            'total_creditado': pedido.total_creditado,
            'moedas_geradas': pedido.moedas_geradas,
            'percentual_bonus': percentual_bonus,
            'status': dados['status_mapping'].get(pedido.status, pedido.status.lower()),
            'metodo_pagamento': dados['metodo_mapping'].get(pedido.metodo, pedido.metodo.lower()),
            'data': pedido.data_criacao,
        })
    
    return render(request, 'accountancy/relatorio_pedidos_pagamentos.html', {
        'relatorio': relatorio,
        'resumo': resumo,
        'page_obj': page_obj,
        'filter_form': filter_form,
    })


@staff_member_required
def relatorio_reconciliacao_wallet(request):
    # Inicializa o formulário de filtros
    filter_form = ReconciliacaoWalletFilterForm(request.GET)
    
    # Obtém todos os dados
    dados = reconciliacao_wallet_transacoes()
    relatorio = dados['relatorio']
    resumo = dados['resumo']
    
    # Aplica os filtros se o formulário for válido
    relatorio_filtrado = []
    if filter_form.is_valid():
        usuario_filter = filter_form.cleaned_data.get('usuario')
        status_filter = filter_form.cleaned_data.get('status')
        diferenca_minima = filter_form.cleaned_data.get('diferenca_minima')
        diferenca_maxima = filter_form.cleaned_data.get('diferenca_maxima')
        
        for item in relatorio:
            # Filtra por usuário
            if usuario_filter and usuario_filter.lower() not in item['usuario'].lower():
                continue
            
            # Filtra por status
            if status_filter and item['status'] != status_filter:
                continue
            
            # Filtra por diferença
            diferenca = item['diferenca']
            if diferenca_minima is not None and diferenca < diferenca_minima:
                continue
            if diferenca_maxima is not None and diferenca > diferenca_maxima:
                continue
            
            relatorio_filtrado.append(item)
    else:
        relatorio_filtrado = relatorio
    
    # Calcula contadores de status para TODOS os dados (sem filtros)
    todos_contadores = {'reconciliado': 0, 'discrepancia': 0, 'em_analise': 0, 'pendente': 0}
    for item_geral in relatorio:
        status_geral = item_geral.get('status')
        if status_geral in todos_contadores:
            todos_contadores[status_geral] += 1
    
    resumo['status_contador'] = todos_contadores
    
    # Paginação
    paginator = Paginator(relatorio_filtrado, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accountancy/relatorio_reconciliacao_wallet.html', {
        'relatorio': list(page_obj),
        'resumo': resumo,
        'page_obj': page_obj,
        'filter_form': filter_form,
    })


@staff_member_required
def dashboard_accountancy(request):
    return render(request, 'accountancy/dashboard.html')
