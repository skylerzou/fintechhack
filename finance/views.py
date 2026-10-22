from django.shortcuts import render
from organizations.services import required_role
from finance.services import PERMISSIONS,list_requests, list_personal, org_fin_view, request_complete, request_accept, request_deny
from finance.models import SpendingReq
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.core.exceptions import ValidationError,PermissionDenied
from django.contrib import messages
# Create your views here.

# library/views.py
VALID_STATUSES = {"all", *SpendingReq.Status.values}   # built from the model's own choices

def request_list(request, organization_slug):           # Django passes the slug; the middleware already used it
    status = request.GET.get("status", "all")
    if status not in VALID_STATUSES:
        status = "all"                          # your decision for bad filter values
    spending_reqs = list_requests(actor=request.user, org=request.org, status=status)
    pending_count = SpendingReq.objects.filter(
        organization=request.org, status=SpendingReq.Status.PENDING
    ).count()
    submitted_count = SpendingReq.objects.filter(
        organization=request.org, status=SpendingReq.Status.SUBMITTED
        ).count()
    return render(request, "finance/request_list.html", {
        "spending_reqs": spending_reqs,
        "status_filter": status,
        "pending_count": pending_count,
        "submitted_count": submitted_count,
    })

@require_POST
def request_complete_view(request, organization_slug, request_id):
    try:
        request_complete(actor = request.user, request_id = request_id, org = request.org)
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, "Request Completed")
    return redirect("request-list", organization_slug = organization_slug)

@require_POST
def request_approve_view(request, organization_slug, request_id):
    try:
        request_accept(actor = request.user, request_id = request_id, org = request.org)
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, "Request Accepted")
    return redirect("request-list", organization_slug = organization_slug)

@require_POST
def request_deny_view(request, organization_slug, request_id):
    try:
        request_deny(actor = request.user, request_id = request_id, org = request.org)
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, "Request Denied")
    return redirect("request-list", organization_slug = organization_slug)



def request_list_personal(request, organization_slug):
    status = request.GET.get("status", "all")
    if status not in VALID_STATUSES:
        status = "all"
    datadict = list_personal(actor = request.user, org = request.org, status = status)
    spending_reqs = datadict["spending_reqs"]
    pending = datadict["pending_count"]
    submitted = datadict["submitted_count"]
    return render(request, "finance/request_personal.html", {
        "spending_reqs": spending_reqs,
        "status_filter": status,
        "pending_count": pending,
        "waiting_reim_count": submitted,
    })  

def org_overview(request, organization_slug):
    return render(request, "finance/overview.html", org_fin_view(actor = request.user, org = request.org))