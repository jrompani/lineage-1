from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from ..models import (
    ItemInflationSnapshot,
    ItemInflationSnapshotDetail,
    ItemInflationCategory,
    ItemInflationStats
)
from apps.lineage.inventory.models import Inventory, InventoryItem, CustomItem
from apps.lineage.inventory.utils.items import get_itens_json
from utils.dynamic_import import get_query_class
from apps.lineage.server.database import LineageDB


def get_item_name(item_id):
    """
    Busca o nome do item primeiro em CustomItem, depois em itens.json
    """
    try:
        custom_item = CustomItem.objects.get(item_id=item_id)
        return custom_item.nome
    except CustomItem.DoesNotExist:
        try:
            itens_data = get_itens_json()
            item_data = itens_data.get(str(item_id), [None])
            return item_data[0] if item_data and item_data[0] else f'Item {item_id}'
        except:
            return f'Item {item_id}'


def enrich_items_with_names(items_list):
    """
    Enriquece uma lista de itens com nomes do CustomItem ou itens.json
    """
    if not items_list:
        return items_list
    
    # Filtra apenas itens com item_id válido
    item_ids = []
    for item in items_list:
        item_id = item.get('item_id')
        if item_id is not None:
            try:
                item_ids.append(int(item_id))
            except (ValueError, TypeError):
                continue
    
    if not item_ids:
        return items_list
    
    # Busca todos os CustomItems de uma vez
    try:
        custom_items = {item.item_id: item.nome for item in CustomItem.objects.filter(item_id__in=item_ids)}
    except:
        custom_items = {}
    
    # Busca itens.json uma vez
    try:
        itens_data = get_itens_json()
    except:
        itens_data = {}
    
    # Enriquece cada item
    for item in items_list:
        item_id = item.get('item_id')
        if item_id is not None:
            try:
                item_id_int = int(item_id)
            except (ValueError, TypeError):
                continue
            
            # Tenta CustomItem primeiro
            if item_id_int in custom_items:
                item['item_name'] = custom_items[item_id_int]
            # Depois tenta itens.json
            elif str(item_id_int) in itens_data:
                item_data = itens_data[str(item_id_int)]
                item['item_name'] = item_data[0] if item_data and item_data[0] else f'Item {item_id_int}'
            # Se não tiver nome ou tiver nome genérico, atualiza
            elif not item.get('item_name') or str(item.get('item_name', '')).startswith('Item '):
                item['item_name'] = get_item_name(item_id_int)
    
    return items_list


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def inflation_dashboard(request):
    """
    Painel principal de inflação de itens.
    Mostra estatísticas gerais e permite criar snapshots.
    """
    LineageInflation = get_query_class("LineageInflation")
    
    # Estatísticas gerais
    try:
        location_summary = LineageInflation.get_items_by_location_summary() or []
    except Exception as e:
        print(f"Erro ao buscar location_summary: {e}")
        location_summary = []
    
    try:
        top_items_raw = LineageInflation.get_top_items_by_quantity(limit=20) or []
        top_items = enrich_items_with_names(top_items_raw)
    except Exception as e:
        print(f"Erro ao buscar top_items: {e}")
        top_items = []
    
    # Calcula totais a partir dos dados reais do servidor
    total_instances = 0
    total_quantity = 0
    if location_summary:
        for loc in location_summary:
            try:
                total_instances += int(loc.get('total_instances', 0) or 0)
                total_quantity += int(loc.get('total_quantity', 0) or 0)
            except (ValueError, TypeError):
                continue
    
    # Conta personagens
    try:
        total_chars_result = LineageDB().select(
            "SELECT COUNT(*) as total FROM characters WHERE accesslevel = '0'"
        )
        if total_chars_result and len(total_chars_result) > 0:
            total_characters = int(total_chars_result[0].get('total', 0) or 0)
        else:
            total_characters = 0
    except Exception as e:
        print(f"Erro ao contar personagens: {e}")
        total_characters = 0
    
    # Snapshots recentes
    recent_snapshots = ItemInflationSnapshot.objects.all()[:10]
    
    # Último snapshot
    last_snapshot = ItemInflationSnapshot.objects.first()
    
    # Estatísticas do site (inventário do site)
    site_items_count = InventoryItem.objects.aggregate(
        total_quantity=models.Sum('quantity'),
        total_items=models.Count('id')
    )
    
    context = {
        'location_summary': location_summary,
        'top_items': top_items,
        'recent_snapshots': recent_snapshots,
        'last_snapshot': last_snapshot,
        'site_items_count': site_items_count,
        # Dados calculados em tempo real
        'total_instances': total_instances,
        'total_quantity': total_quantity,
        'total_characters': total_characters,
    }
    
    return render(request, 'server/inflation/dashboard.html', context)


@staff_required
def create_snapshot(request):
    """
    Cria um snapshot do estado atual dos itens no servidor.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        LineageInflation = get_query_class("LineageInflation")
        
        # Verifica se já existe snapshot para hoje
        today = date.today()
        if ItemInflationSnapshot.objects.filter(snapshot_date=today).exists():
            return JsonResponse({
                'error': _('Já existe um snapshot para hoje. Aguarde até amanhã ou delete o snapshot existente.')
            }, status=400)
        
        # Busca dados do servidor
        items_summary = LineageInflation.get_items_summary_by_category()
        location_summary = LineageInflation.get_items_by_location_summary()
        
        # Conta personagens
        total_chars = LineageDB().select(
            "SELECT COUNT(*) as total FROM characters WHERE accesslevel = '0'"
        )
        total_characters = total_chars[0]['total'] if total_chars else 0
        
        # Calcula totais
        total_instances = sum(item['total_instances'] for item in items_summary)
        total_quantity = sum(item['total_quantity'] for item in items_summary)
        
        with transaction.atomic():
            # Cria snapshot
            snapshot = ItemInflationSnapshot.objects.create(
                snapshot_date=today,
                total_characters=total_characters,
                total_items_instances=total_instances,
                total_items_quantity=total_quantity,
                notes=request.POST.get('notes', '')
            )
            
            # Cria detalhes do snapshot
            categories = {
                cat.name: cat for cat in ItemInflationCategory.objects.all()
            }
            
            # Enriquece items_summary com nomes corretos
            items_summary = enrich_items_with_names(items_summary)
            
            for item_data in items_summary:
                # Determina categoria
                category = None
                item_id = item_data.get('item_id')
                for cat_name, cat_obj in categories.items():
                    if item_id in cat_obj.item_ids:
                        category = cat_obj
                        break
                
                ItemInflationSnapshotDetail.objects.create(
                    snapshot=snapshot,
                    item_id=item_id,
                    item_name=item_data.get('item_name', get_item_name(item_id)),
                    location=item_data.get('location', 'INVENTORY'),
                    quantity=item_data.get('total_quantity', 0),
                    instances=item_data.get('total_instances', 0),
                    unique_owners=item_data.get('unique_owners', 0),
                    category=category
                )
            
            # Adiciona itens do site
            site_items = InventoryItem.objects.values('item_id', 'item_name').annotate(
                total_quantity=models.Sum('quantity'),
                total_instances=models.Count('id'),
                unique_owners=models.Count('inventory__user', distinct=True)
            )
            
            for site_item in site_items:
                category = None
                item_id = site_item['item_id']
                for cat_name, cat_obj in categories.items():
                    if item_id in cat_obj.item_ids:
                        category = cat_obj
                        break
                
                ItemInflationSnapshotDetail.objects.create(
                    snapshot=snapshot,
                    item_id=item_id,
                    item_name=site_item.get('item_name', f'Item {item_id}'),
                    location='SITE',
                    quantity=site_item.get('total_quantity', 0),
                    instances=site_item.get('total_instances', 0),
                    unique_owners=site_item.get('unique_owners', 0),
                    category=category
                )
        
        messages.success(request, _('Snapshot criado com sucesso!'))
        return JsonResponse({
            'success': True,
            'snapshot_id': snapshot.id,
            'message': _('Snapshot criado com sucesso!')
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@staff_required
def snapshot_detail(request, snapshot_id):
    """
    Detalhes de um snapshot específico.
    """
    snapshot = get_object_or_404(ItemInflationSnapshot, id=snapshot_id)
    details = snapshot.details.all().order_by('-quantity')[:100]
    
    # Agrupa por localização
    by_location = {}
    for detail in snapshot.details.all():
        loc = detail.location
        if loc not in by_location:
            by_location[loc] = {
                'total_quantity': 0,
                'total_instances': 0,
                'unique_items': set(),
                'details': []
            }
        by_location[loc]['total_quantity'] += detail.quantity
        by_location[loc]['total_instances'] += detail.instances
        by_location[loc]['unique_items'].add(detail.item_id)
        by_location[loc]['details'].append(detail)
    
    # Converte sets para contagem
    for loc in by_location:
        by_location[loc]['unique_items'] = len(by_location[loc]['unique_items'])
    
    context = {
        'snapshot': snapshot,
        'details': details,
        'by_location': by_location,
    }
    
    return render(request, 'server/inflation/snapshot_detail.html', context)


@staff_required
def inflation_comparison(request):
    """
    Compara dois snapshots para verificar mudanças na inflação.
    """
    snapshots = ItemInflationSnapshot.objects.all().order_by('-snapshot_date')
    
    snapshot_from_id = request.GET.get('from')
    snapshot_to_id = request.GET.get('to')
    
    comparison_data = None
    
    if snapshot_from_id and snapshot_to_id:
        snapshot_from = get_object_or_404(ItemInflationSnapshot, id=snapshot_from_id)
        snapshot_to = get_object_or_404(ItemInflationSnapshot, id=snapshot_to_id)
        
        # Busca detalhes
        details_from = {
            (d.item_id, d.location): d for d in snapshot_from.details.all()
        }
        details_to = {
            (d.item_id, d.location): d for d in snapshot_to.details.all()
        }
        
        # Compara
        comparison_items = []
        all_keys = set(details_from.keys()) | set(details_to.keys())
        
        for key in all_keys:
            item_id, location = key
            from_detail = details_from.get(key)
            to_detail = details_to.get(key)
            
            from_qty = from_detail.quantity if from_detail else 0
            to_qty = to_detail.quantity if to_detail else 0
            change = to_qty - from_qty
            
            if from_qty > 0:
                change_pct = (change / from_qty) * 100
            else:
                change_pct = 100 if to_qty > 0 else 0
            
            comparison_items.append({
                'item_id': item_id,
                'item_name': to_detail.item_name if to_detail else (from_detail.item_name if from_detail else f'Item {item_id}'),
                'location': location,
                'from_quantity': from_qty,
                'to_quantity': to_qty,
                'change': change,
                'change_percentage': round(change_pct, 2),
                'category': to_detail.category if to_detail else (from_detail.category if from_detail else None)
            })
        
        comparison_items.sort(key=lambda x: abs(x['change']), reverse=True)
        
        comparison_data = {
            'from': snapshot_from,
            'to': snapshot_to,
            'items': comparison_items[:100],  # Top 100 mudanças
        }
    
    context = {
        'snapshots': snapshots,
        'comparison': comparison_data,
    }
    
    return render(request, 'server/inflation/comparison.html', context)


@staff_required
def inflation_categories(request):
    """
    Gerencia categorias de itens para análise de inflação.
    """
    categories = ItemInflationCategory.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            item_ids_str = request.POST.get('item_ids', '')
            color = request.POST.get('color', '#000000')
            
            # Converte string de IDs para lista
            item_ids = [int(id.strip()) for id in item_ids_str.split(',') if id.strip().isdigit()]
            
            ItemInflationCategory.objects.create(
                name=name,
                description=description,
                item_ids=item_ids,
                color=color
            )
            messages.success(request, _('Categoria criada com sucesso!'))
            return redirect('inflation_categories')
        
        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            category = get_object_or_404(ItemInflationCategory, id=cat_id)
            category.delete()
            messages.success(request, _('Categoria deletada com sucesso!'))
            return redirect('inflation_categories')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'server/inflation/categories.html', context)


@staff_required
def delete_snapshot(request, snapshot_id):
    """
    Deleta um snapshot.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    snapshot = get_object_or_404(ItemInflationSnapshot, id=snapshot_id)
    snapshot.delete()
    
    messages.success(request, _('Snapshot deletado com sucesso!'))
    return JsonResponse({'success': True})

