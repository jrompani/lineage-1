from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    # Lista de personagens à venda
    path('', views.marketplace_list, name='list'),
    
    # Detalhes de um personagem
    path('character/<int:transfer_id>/', views.character_detail, name='character_detail'),
    
    # Listar personagem para venda
    path('sell/', views.sell_character, name='sell'),
    
    # Comprar personagem
    path('buy/<int:transfer_id>/', views.buy_character, name='buy'),
    
    # Cancelar venda
    path('cancel/<int:transfer_id>/', views.cancel_sale, name='cancel'),
    
    # Minhas vendas
    path('my-sales/', views.my_sales, name='my_sales'),
    
    # Minhas compras
    path('my-purchases/', views.my_purchases, name='my_purchases'),
]

