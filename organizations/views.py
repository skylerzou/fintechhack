from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from organizations.services import get_memberships,create_org
from django.shortcuts import redirect
from organizations.forms import OrgCreationForm
from django.core.exceptions import ValidationError,PermissionDenied
from django.contrib import messages
from organizations.services import change_role, get_org_admin, join_org, regen_join_code, overspend_adjustment
from organizations.forms import RoleChangeForm, JoinOrgForm,OverSpendForm
from django.views.decorators.http import require_POST


# Create your views here.

@login_required
def org_picker(request): #request is user sent object
    memberships = get_memberships(actor = request.user)
    return render(request, "organizations/org_picker.html", {"memberships": memberships})

@login_required
def org_creator(request):
    if request.method == "POST":
        form = OrgCreationForm(request.POST)
        if form.is_valid():
            try:
                org = create_org(actor = request.user, name = form.cleaned_data["name"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Organization Created")
                return redirect("org-fin-overview", organization_slug = org.slug)
    else:
        form = OrgCreationForm()
    return render(request, "organizations/org-creator.html", {"form": form})

@require_POST
def change_role_view(request, organization_slug, membership_id):
    form = RoleChangeForm(request.POST)
    if form.is_valid():
        try:
            change_role(actor = request.user, org = request.org, membership_id = membership_id, new_role = form.cleaned_data["role"])
        except ValidationError as e:
            messages.error(request, e.messages[0])
        else:
            messages.success(request, "Role Changed")
    else:
        messages.error(request, "Invalid Role")
    return redirect("member-list", organization_slug = organization_slug)

def member_list_view(request, organization_slug):
    return render(request, "organizations/members.html", get_org_admin(actor=request.user, org=request.org))

@login_required
def join_via_code(request, code=None):
    if request.method == "POST":
            form = JoinOrgForm(request.POST)
            if form.is_valid():
                try:
                    org = join_org(actor = request.user, code = form.cleaned_data["code"])
                except ValidationError as e:
                    form.add_error(None, e.messages[0])
                else:
                    messages.success(request, "Organization Joined")
                    return redirect("request-list-mine", organization_slug = org.slug)
    else:
        form = JoinOrgForm(initial={"code": code})
    return render(request, "organizations/join.html", {"form": form})

@require_POST
def regen_code(request, organization_slug):
    try: 
        regen_join_code(actor = request.user, org = request.org)
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, "Join Code Changed")
    return redirect("member-list", organization_slug = organization_slug)

def overspend_adjust_view(request, organization_slug):
    if request.method == "POST":
        form = OverSpendForm(request.POST)
        if form.is_valid():
            try:
                overspend_adjustment(actor = request.user, org = request.org, new_limit = form.cleaned_data["overspend_limit"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Overspend Limit Adjusted")
                return redirect("org-fin-overview", organization_slug= organization_slug)
    else:
        form = OverSpendForm(initial={"overspend_limit": request.org.overspend_limit})
    return render(request, "organizations/overspend-adjust.html", {"form" : form})
 