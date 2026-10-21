
from django.urls import path
from finance import views

urlpatterns = [
    path('requests/', views.request_list, name='request-list'),
    path('prequests/',views.request_list_personal, name = 'request-list-personal')
    path('overview/', views.org_overview, name = '')
]