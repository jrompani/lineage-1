from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    WikiPage, WikiPageTranslation,
    WikiUpdate, WikiUpdateTranslation,
)
from core.admin import BaseModelAdmin, BaseInlineAdmin


# ============================================================================
# WIKI PAGES - Páginas do Wiki (Index, Menu e Conteúdo)
# ============================================================================

class WikiPageTranslationInline(BaseInlineAdmin):
    model = WikiPageTranslation
    fields = ('language', 'title', 'subtitle', 'summary', 'content', 'meta_description')
    verbose_name = _('Tradução da Página')
    verbose_name_plural = _('Traduções da Página')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['language'].widget.attrs.update({
            'class': 'form-control',
            'style': 'width: 150px;'
        })
        formset.form.base_fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Título da Página'),
            'style': 'width: 100%;'
        })
        formset.form.base_fields['subtitle'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Subtítulo (opcional)'),
            'style': 'width: 100%;'
        })
        formset.form.base_fields['summary'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Resumo para listas'),
            'rows': 3,
            'style': 'width: 100%;'
        })
        formset.form.base_fields['meta_description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Descrição para SEO'),
            'rows': 2,
            'style': 'width: 100%;'
        })
        return formset


@admin.register(WikiPage)
class WikiPageAdmin(BaseModelAdmin):
    """Admin para gerenciar todas as páginas do Wiki"""
    list_display = ('get_title', 'content_type', 'slug', 'order', 'is_active', 'is_menu_item', 'get_languages', 'created_at')
    list_filter = ('is_active', 'is_menu_item', 'content_type', 'created_at')
    search_fields = ('translations__title', 'translations__content', 'translations__summary')
    ordering = ('order', 'content_type', 'id')
    list_editable = ('order', 'is_active', 'is_menu_item', 'content_type')
    inlines = [WikiPageTranslationInline]
    
    fieldsets = (
        (_('Configurações da Página'), {
            'fields': ('content_type', 'slug', 'order', 'is_active', 'is_menu_item'),
            'description': _('Configure o tipo, slug e visibilidade da página')
        }),
        (_('Navegação'), {
            'fields': ('parent_page', 'icon'),
            'description': _('Configure a hierarquia e ícone da página'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_pages', 'deactivate_pages', 'make_menu_items', 'remove_menu_items', 'reorder_pages']

    def get_title(self, obj):
        """Retorna o título em português ou o primeiro disponível"""
        pt_translation = obj.translations.filter(language='pt').first()
        if pt_translation:
            return pt_translation.title
        first_translation = obj.translations.first()
        if first_translation:
            return format_html(
                '<span style="color: #666;">[{}] {}</span>',
                first_translation.language.upper(),
                first_translation.title
            )
        return _('Sem tradução')
    get_title.short_description = _('Título')

    def get_languages(self, obj):
        """Mostra os idiomas disponíveis"""
        languages = obj.translations.values_list('language', flat=True)
        if languages:
            badges = []
            for lang in languages:
                color = '#28a745' if lang == 'pt' else '#17a2b8'
                badges.append(
                    format_html(
                        '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin: 1px;">{}</span>',
                        color, lang.upper()
                    )
                )
            return format_html(' '.join(badges))
        return format_html(
            '<span style="color: #dc3545; font-size: 11px;">{}</span>',
            _('Sem traduções')
        )
    get_languages.short_description = _('Idiomas')

    def activate_pages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('{} páginas foram ativadas.').format(updated))
    activate_pages.short_description = _('Ativar páginas selecionadas')

    def deactivate_pages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('{} páginas foram desativadas.').format(updated))
    deactivate_pages.short_description = _('Desativar páginas selecionadas')

    def make_menu_items(self, request, queryset):
        updated = queryset.update(is_menu_item=True)
        self.message_user(request, _('{} páginas foram adicionadas ao menu.').format(updated))
    make_menu_items.short_description = _('Adicionar ao menu')

    def remove_menu_items(self, request, queryset):
        updated = queryset.update(is_menu_item=False)
        self.message_user(request, _('{} páginas foram removidas do menu.').format(updated))
    remove_menu_items.short_description = _('Remover do menu')

    def reorder_pages(self, request, queryset):
        """Reordena as páginas baseado na ordem atual"""
        for i, page in enumerate(queryset.order_by('order'), 1):
            page.order = i
            page.save()
        self.message_user(request, _('Ordem das páginas foi reorganizada.'))
    reorder_pages.short_description = _('Reorganizar ordem')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')


# ============================================================================
# WIKI UPDATES - Atualizações do servidor
# ============================================================================

class WikiUpdateTranslationInline(BaseInlineAdmin):
    model = WikiUpdateTranslation
    fields = ('language', 'title', 'content', 'changelog')
    verbose_name = _('Tradução da Atualização')
    verbose_name_plural = _('Traduções da Atualização')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['language'].widget.attrs.update({
            'class': 'form-control',
            'style': 'width: 150px;'
        })
        formset.form.base_fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Título da Atualização'),
            'style': 'width: 100%;'
        })
        return formset


@admin.register(WikiUpdate)
class WikiUpdateAdmin(BaseModelAdmin):
    """Admin para gerenciar atualizações do servidor"""
    list_display = ('version', 'release_date', 'is_active', 'is_major', 'get_languages', 'created_at')
    list_filter = ('is_active', 'is_major', 'release_date', 'created_at')
    search_fields = ('version', 'translations__title', 'translations__content')
    ordering = ('-release_date', '-version')
    list_editable = ('is_active', 'is_major')
    inlines = [WikiUpdateTranslationInline]
    
    fieldsets = (
        (_('Informações da Atualização'), {
            'fields': ('version', 'release_date', 'is_active', 'is_major'),
            'description': _('Configure a versão e data de lançamento')
        }),
    )
    
    actions = ['activate_updates', 'deactivate_updates', 'mark_as_major', 'mark_as_minor']

    def get_languages(self, obj):
        """Mostra os idiomas disponíveis"""
        languages = obj.translations.values_list('language', flat=True)
        if languages:
            badges = []
            for lang in languages:
                color = '#28a745' if lang == 'pt' else '#17a2b8'
                badges.append(
                    format_html(
                        '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin: 1px;">{}</span>',
                        color, lang.upper()
                    )
                )
            return format_html(' '.join(badges))
        return format_html(
            '<span style="color: #dc3545; font-size: 11px;">{}</span>',
            _('Sem traduções')
        )
    get_languages.short_description = _('Idiomas')

    def activate_updates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('{} atualizações foram ativadas.').format(updated))
    activate_updates.short_description = _('Ativar atualizações selecionadas')

    def deactivate_updates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('{} atualizações foram desativadas.').format(updated))
    deactivate_updates.short_description = _('Desativar atualizações selecionadas')

    def mark_as_major(self, request, queryset):
        updated = queryset.update(is_major=True)
        self.message_user(request, _('{} atualizações foram marcadas como principais.').format(updated))
    mark_as_major.short_description = _('Marcar como principais')

    def mark_as_minor(self, request, queryset):
        updated = queryset.update(is_major=False)
        self.message_user(request, _('{} atualizações foram marcadas como secundárias.').format(updated))
    mark_as_minor.short_description = _('Marcar como secundárias')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')


# ============================================================================
# ADMIN SITE CONFIGURATION
# ============================================================================

# Configurar o admin site para o Wiki
admin.site.site_header = _('Administração do Wiki')
admin.site.site_title = _('Wiki Admin')
admin.site.index_title = _('Gerenciamento do Wiki')
