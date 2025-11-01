from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _

from ..models import Prize, Item
from ..forms import PrizeManagerForm


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def dashboard(request):
    form = PrizeManagerForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = PrizeManagerForm(request.POST)
            if form.is_valid():
                prize = form.save(commit=False)
                # Preenche legados para compatibilidade
                if prize.item:
                    prize.name = prize.item.name
                    prize.legacy_item_code = prize.item.item_id
                    prize.enchant = prize.item.enchant
                    prize.rarity = prize.item.rarity
                prize.save()
                messages.success(request, _('Prêmio adicionado à roleta.'))
                return redirect('games:roulette_manager')
            else:
                messages.error(request, _('Corrija os erros do formulário.'))

        elif action == 'delete':
            pid = request.POST.get('prize_id')
            prize = get_object_or_404(Prize, id=pid)
            prize.delete()
            messages.success(request, _('Prêmio removido.'))
            return redirect('games:roulette_manager')

        elif action == 'update_weight':
            pid = request.POST.get('prize_id')
            weight = request.POST.get('weight')
            prize = get_object_or_404(Prize, id=pid)
            try:
                prize.weight = max(1, int(weight))
                prize.save(update_fields=['weight'])
                messages.success(request, _('Peso atualizado.'))
            except Exception as e:
                messages.error(request, str(e))
            return redirect('games:roulette_manager')

    prizes = Prize.objects.select_related('item').all().order_by('-weight', 'id')
    return render(request, 'roulette/manager/dashboard.html', {
        'form': form,
        'prizes': prizes,
    })


