from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import News, NewsTranslation
from core.admin import BaseModelAdmin
from .forms import NewsForm, NewsTranslationForm
from django import forms


class NewsTranslationInline(admin.StackedInline):
    model = NewsTranslation
    form = NewsTranslationForm
    fields = ['language', 'title', 'summary', 'content']
    verbose_name = _('Tradução')
    verbose_name_plural = _('Traduções')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(NewsTranslationInline, self).get_formset(request, obj, **kwargs)
        formset.form.base_fields['language'].widget.attrs.update({
            'class': 'form-control',
            'style': 'width: 150px;'
        })
        formset.form.base_fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Título'),
            'style': 'width: 100%;'
        })
        formset.form.base_fields['summary'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Resumo'),
            'rows': 3,
            'style': 'width: 100%;'
        })
        # Não configuramos o widget do content pois o CKEditor5 já tem seus próprios estilos
        return formset


@admin.register(News)
class NewsAdmin(BaseModelAdmin):
    form = NewsForm
    inlines = [NewsTranslationInline]

    list_display = ('get_title', 'author', 'pub_date', 'is_published', 'is_private', 'get_languages', 'created_at')
    list_filter = ('is_published', 'is_private', 'pub_date', 'created_at', 'author', 'translations__language')
    search_fields = ('translations__title', 'translations__content', 'translations__summary', 'author__username')
    list_editable = ('is_published', 'is_private')
    ordering = ('-pub_date', '-created_at')
    exclude = ('author',)
    
    fieldsets = (
        (_('Configurações de Publicação'), {
            'fields': ('pub_date', 'is_published', 'is_private'),
            'description': _('Configure quando e como a notícia será exibida')
        }),
    )
    
    actions = ['publish_selected', 'unpublish_selected', 'make_private', 'make_public']

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
    get_title.admin_order_field = 'translations__title'

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

    def publish_selected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_published=True, pub_date=timezone.now())
        self.message_user(request, _('{} notícias foram publicadas.').format(updated))
    publish_selected.short_description = _('Publicar notícias selecionadas')

    def unpublish_selected(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, _('{} notícias foram despublicadas.').format(updated))
    unpublish_selected.short_description = _('Despublicar notícias selecionadas')

    def make_private(self, request, queryset):
        updated = queryset.update(is_private=True)
        self.message_user(request, _('{} notícias foram tornadas privadas.').format(updated))
    make_private.short_description = _('Tornar privadas')

    def make_public(self, request, queryset):
        updated = queryset.update(is_private=False)
        self.message_user(request, _('{} notícias foram tornadas públicas.').format(updated))
    make_public.short_description = _('Tornar públicas')

    def save_model(self, request, obj, form, change):
        if not change or not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.news = form.instance
            instance.save()
        formset.save_m2m()
        
        # Generate or validate slug after translations are saved
        news_obj = form.instance
        from django.utils.text import slugify
        pt_translation = news_obj.translations.filter(language='pt').first()
        
        if pt_translation:
            if not news_obj.slug:
                # Auto-generate slug from title
                base_slug = slugify(pt_translation.title)
                news_obj.slug = self._get_unique_slug(base_slug, news_obj.pk)
                news_obj.save()
            else:
                # Validate manually entered slug and make it unique if needed
                current_slug = news_obj.slug
                unique_slug = self._get_unique_slug(current_slug, news_obj.pk)
                if current_slug != unique_slug:
                    news_obj.slug = unique_slug
                    news_obj.save()
                    # Add a message to inform the user about the slug change
                    from django.contrib import messages
                    messages.warning(
                        request,
                        _('O slug foi alterado de "{}" para "{}" para evitar duplicação.').format(
                            current_slug, unique_slug
                        )
                    )

    def _get_unique_slug(self, base_slug, news_pk=None):
        """Generate a unique slug by appending a number if necessary"""
        slug = base_slug
        counter = 1
        
        while True:
            # Check if slug exists, excluding current news object if editing
            queryset = News.objects.filter(slug=slug)
            if news_pk:
                queryset = queryset.exclude(pk=news_pk)
            
            if not queryset.exists():
                return slug
            
            # If slug exists, append counter and try again
            slug = f"{base_slug}-{counter}"
            counter += 1

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')

    class Media:
        css = {
            'all': ('admin/css/news_admin.css',)
        }
        js = ('admin/js/news_admin.js',)
