from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _

from ..models import Monster, RewardItem
from ..forms import MonsterManagerForm, RewardItemManagerForm


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff)(view)


@staff_required
def dashboard(request):
    monster_form = MonsterManagerForm()
    reward_form = RewardItemManagerForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_monster':
            monster_form = MonsterManagerForm(request.POST, request.FILES)
            if monster_form.is_valid():
                monster_form.save()
                messages.success(request, _('Monstro adicionado.'))
                return redirect('games:economy_manager')
            else:
                messages.error(request, _('Corrija os erros do formulário do monstro.'))

        elif action == 'delete_monster':
            mid = request.POST.get('monster_id')
            mon = get_object_or_404(Monster, id=mid)
            mon.delete()
            messages.success(request, _('Monstro removido.'))
            return redirect('games:economy_manager')

        elif action == 'update_monster':
            mid = request.POST.get('monster_id')
            mon = get_object_or_404(Monster, id=mid)
            form = MonsterManagerForm(request.POST, request.FILES, instance=mon)
            if form.is_valid():
                form.save()
                messages.success(request, _('Monstro atualizado.'))
            else:
                messages.error(request, _('Corrija os erros do formulário.'))
            return redirect('games:economy_manager')

        elif action == 'set_reward':
            # define/recria a recompensa padrão usada no +10
            RewardItem.objects.all().delete()
            reward_form = RewardItemManagerForm(request.POST)
            if reward_form.is_valid():
                reward = reward_form.save(commit=False)
                if reward.item:
                    # preencher campos legados para compatibilidade
                    reward.name = reward.item.name
                    reward.legacy_item_code = reward.item.item_id
                    reward.enchant = reward.item.enchant
                reward.save()
                messages.success(request, _('Recompensa padrão atualizada.'))
                return redirect('games:economy_manager')
            else:
                messages.error(request, _('Corrija os erros do formulário de recompensa.'))

    monsters = Monster.objects.all().order_by('level', 'name')
    reward = RewardItem.objects.select_related('item').first()
    return render(request, 'economy/manager/dashboard.html', {
        'monsters': monsters,
        'monster_form': monster_form,
        'reward': reward,
        'reward_form': reward_form,
    })


