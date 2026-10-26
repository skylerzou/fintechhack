from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from organizations.services import get_memberships,create_org
from django.shortcuts import redirect
from organizations.forms import OrgCreationForm
from django.core.exceptions import ValidationError,PermissionDenied
from django.contrib import messages

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