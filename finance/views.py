from django.shortcuts import render
from organizations.services import required_role
from finance.services import PERMISSIONS,list_requests, list_personal, org_fin_view, request_complete, request_approve, request_deny, request_spending, request_reim, get_own_request, bal_adjustment, ledger_list, set_bal, count_pending
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.core.exceptions import ValidationError,PermissionDenied
from django.contrib import messages
from finance.forms import SpendingRequestForm, SpendingRequestReimForm, BalAdjustmentForm, BalSetForm, ReimChalForm
from finance.models import SpendingReq

# Create your views here.

VALID_STATUSES = {"all", *SpendingReq.Status.values}   # built from the model's own choices
#add working balance
def request_list(request, organization_slug):           # Django passes the slug; the middleware already used it
    status = request.GET.get("status", "all")
    if status not in VALID_STATUSES:
        status = "all"                          # your decision for bad filter values
    spending_reqs = list_requests(actor=request.user, org=request.org, status=status)
    datadict = org_fin_view(actor = request.user, org = request.org)
    working = datadict["working_balance"]
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
        "working_balance": working,
    })

def ledger_list_view(request, organization_slug):
    ledgers = ledger_list(actor = request.user, org = request.org)
    return render(request, "finance/ledger_list.html", {"ledgers": ledgers})

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
        request_approve(actor = request.user, request_id = request_id, org = request.org)
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

def spending_request_new(request, organization_slug):
    if request.method == "POST":
        form = SpendingRequestForm(request.POST)
        if form.is_valid():
            try:
                request_spending(actor = request.user, org = request.org, title=form.cleaned_data["title"], spend = form.cleaned_data["spend"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Request Submitted")
                return redirect("request-list-mine", organization_slug= organization_slug)
    else:
        #its GET
        form = SpendingRequestForm()
    return render(request, "finance/spending_new.html", {"form": form})

def spending_request_reim(request, request_id, organization_slug):
    req = get_own_request(actor = request.user, org = request.org, request_id = request_id)
    if request.method == "POST":
        form = SpendingRequestReimForm(request.POST)
        if form.is_valid():
            try:
                request_reim(actor = request.user, org = request.org, request_id= request_id, reimamount = form.cleaned_data["reimamount"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Reimbursement Request Submitted")
                return redirect("request-list-mine", organization_slug= organization_slug)
    else:
        form = SpendingRequestReimForm()
    return render(request, "finance/reim_new.html", {"form" : form, "req" : req})

def org_overview(request, organization_slug):
    datadict = org_fin_view(actor = request.user, org = request.org)
    real = datadict["true_balance"]
    pendreim = datadict["pending_reim"]
    approved = datadict["curr_approved"]
    pendapp = datadict["pending_approved"]
    working = datadict["working_balance"]
    points = datadict["points"]

    return render(request, "finance/overview.html", {"true_balance": real, "pending_reim": pendreim, "curr_approved":approved, "pending_approved":pendapp, "working_balance":working, "points": points })

def bal_adjustment_view(request, organization_slug):
    if request.method == "POST":
        form = BalAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                bal_adjustment(actor = request.user, org = request.org, adjustment =form.cleaned_data["adjustment"], title =form.cleaned_data["title"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Balance Adjusted")
                return redirect('org-fin-overview', organization_slug = organization_slug)
    else:
        form = BalAdjustmentForm()
    return render(request, "finance/bal_adjustment.html", {"form" : form})

def bal_set_view(request, organization_slug):
    if request.method == "POST":
        form = BalSetForm(request.POST)
        if form.is_valid():
            try:
                set_bal(actor = request.user, org = request.org, target = form.cleaned_data["new_balance"])
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                messages.success(request, "Balance Set")
                return redirect('org-fin-overview', organization_slug = organization_slug)
    else:
        form = BalSetForm()
    return render(request, "finance/bal_set.html", {"form" : form})

def pending_badge(request, organization_slug):
    count = count_pending(actor=request.user, org = request.org)
    return render(request, "finance/_pending_badge.html", {"count": count})

# def request_chal_view(request, request_id, organization_slug):
#     if request.method == "POST":
#         form = ReimChalForm(request.POST)
#         if form.is_valid():
#             try:
#                 reim_challenge(actor = request.user, org = request.org, newreim = form.cleaned_data["reimamount"], request_id=request_id)
#             except ValidationError as e:
#                 form.add_error(None, e.messages[0])
#             else:
#                 messages.success(request, "Reimbursement Challenged")
#                 return redirect("request-list", organization_slug = organization_slug)
#     else:
#         form = ReimChalForm()
#     return render(request, "finance/request_chal.html", {"form": form})