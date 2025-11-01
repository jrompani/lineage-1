from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from ..models import DailyBonusSeason, DailyBonusPoolEntry, DailyBonusDay
from ..forms import DailyBonusSeasonForm, DailyBonusPoolEntryForm, DailyBonusDayForm


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def manager_dashboard(request):
    season = DailyBonusSeason.objects.filter(is_active=True).first() or DailyBonusSeason.objects.order_by('-created_at').first()

    season_form = DailyBonusSeasonForm(instance=season)
    pool_form = DailyBonusPoolEntryForm()
    day_form = DailyBonusDayForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'save_season':
                instance = season if season else None
                season_form = DailyBonusSeasonForm(request.POST, instance=instance)
                if season_form.is_valid():
                    season = season_form.save()
                    messages.success(request, _('Temporada salva com sucesso.'))
                    return redirect('games:daily_bonus_manager')
                else:
                    messages.error(request, _('Corrija os erros no formulário da temporada.'))

            elif action == 'add_pool':
                if not season:
                    messages.error(request, _('Crie/salve uma temporada antes de adicionar itens ao pool.'))
                else:
                    pool_form = DailyBonusPoolEntryForm(request.POST)
                    if pool_form.is_valid():
                        entry = pool_form.save(commit=False)
                        entry.season = season
                        entry.save()
                        messages.success(request, _('Item adicionado ao pool.'))
                        return redirect('games:daily_bonus_manager')
                    else:
                        messages.error(request, _('Corrija os erros no formulário do pool.'))

            elif action == 'delete_pool':
                entry_id = request.POST.get('entry_id')
                entry = get_object_or_404(DailyBonusPoolEntry, id=entry_id)
                entry.delete()
                messages.success(request, _('Item removido do pool.'))
                return redirect('games:daily_bonus_manager')

            elif action == 'save_day':
                if not season:
                    messages.error(request, _('Crie/salve uma temporada antes de configurar os dias.'))
                else:
                    day = int(request.POST.get('day_of_month'))
                    db_day, _ = DailyBonusDay.objects.get_or_create(season=season, day_of_month=day)
                    day_form = DailyBonusDayForm(request.POST, instance=db_day)
                    if day_form.is_valid():
                        day_form.save()
                        messages.success(request, _('Dia atualizado.'))
                        return redirect('games:daily_bonus_manager')
                    else:
                        messages.error(request, _('Corrija os erros no formulário do dia.'))

        except Exception as e:
            messages.error(request, str(e))

    pool_entries = DailyBonusPoolEntry.objects.filter(season=season) if season else []
    days = DailyBonusDay.objects.filter(season=season) if season else []
    day_map = {d.day_of_month: d for d in days}

    context = {
        'season': season,
        'season_form': season_form,
        'pool_form': pool_form,
        'pool_entries': pool_entries,
        'day_form': day_form,
        'day_map': day_map,
        'days_range': list(range(1, 32)),
    }
    return render(request, 'daily_bonus/manager/dashboard.html', context)


