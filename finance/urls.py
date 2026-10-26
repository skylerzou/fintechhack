
from django.urls import path
from finance import views

urlpatterns = [
    path('requests/', views.request_list, name='request-list'),
    path('requests/mine/',views.request_list_personal, name = 'request-list-mine'),
    path('overview/', views.org_overview, name = 'org-fin-overview'),
    path('requests/<int:request_id>/approve/', views.request_approve_view, name = 'request-approve'),
    path('requests/<int:request_id>/deny/', views.request_deny_view, name =  'request-deny'),
    path('requests/<int:request_id>/complete/', views.request_complete_view, name = 'request-complete'),
    path('requests/<int:request_id>/reimburse/', views.spending_request_reim, name = 'request-reim'),
    path('requests/mine/create/', views.spending_request_new, name = 'request-create')
]