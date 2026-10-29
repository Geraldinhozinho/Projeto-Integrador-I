

from django.urls import path
from .views import Index, bolsas, bolsistas, agendas, frequencia
urlpatterns = [
    path('', Index, name = 'index' ),
    path('bolsas', bolsas, name = 'bolsas' ),
    path('bolsistas', bolsistas, name = 'bolsistas' ),
    path('agendas', agendas, name = 'agendas' ),
    path('frequencia', frequencia, name = 'frequencia' ),
]