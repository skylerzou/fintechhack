from django.shortcuts import render
from organizations.services import required_role
from finance.services import PERMISSIONS,list_requests, list_personal, org_fin_view
from finance.models import SpendingReq
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

def request_list_personal(request, organization_slug):
    status = request.GET.get("status", "all")
    if status not in VALID_STATUSES:
        status = "all"
    spending_reqs = list_personal(actor = request.user, org = request.org, status = status)
    pending_count = SpendingReq.objects.filter(organization=request.org, status=SpendingReq.Status.PENDING).count()
    submitted_count = SpendingReq.objects.filter(organization=request.org, status=SpendingReq.Status.SUBMITTED).count()
    return render(request, "finance/request_personal.html", {
        "spending_reqs": spending_reqs,
        "status_filter": status,
        "pending_count": pending_count,
        "submitted_count": submitted_count,
    })

def org_overview(request, organization_slug):
    return render(request, "finance/overview.html", org_fin_view(actor = request.user, org = request.org))