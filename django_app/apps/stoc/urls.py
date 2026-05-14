from django.urls import path
from . import views

app_name = 'stoc'

urlpatterns = [
    path('', views.index, name='index'),
    path('expeditie/', views.expeditie, name='expeditie'),
    path('rapoarte/', views.rapoarte, name='rapoarte'),
    path('superviz/', views.superviz, name='superviz'),
    path('export/<str:tip>/', views.export_excel, name='export_excel'),
    path('set-nava/', views.set_nava, name='set_nava'),
    path('borderou/', views.export_borderou, name='export_borderou'),
]
