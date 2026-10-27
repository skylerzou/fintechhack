from django.urls import path
from . import views

urlpatterns = [
    # organizations/urls.py, included at ""
    path("", views.org_picker, name="org-picker"),
    path("orgs/<slug:organization_slug>/members/", views.member_list_view, name="member-list"),
    path("new-org/", views.org_creator, name = "org-create"),
    path("orgs/<slug:organization_slug>/members/<int:membership_id>/role/", views.change_role_view, name = "member-change-role"),
    path("join/", views.join_via_code, name = "join"),
    path("join/<str:code>/", views.join_via_code, name = "join-code"),
    path("orgs/<slug:organization_slug>/members/regen-code/", views.regen_code, name = "regen-code"),
     path("orgs/<slug:organization_slug>/overspend-adjustment/", views.overspend_adjust_view, name = "overspend-adjust"),

]