from decimal import Decimal
from django.db.models import Sum, When, F, Case, DecimalField
from finance.models import SpendingReq, LedgerEntry
from django.db.models.functions import Coalesce
from organizations.models import Membership, Organization
from organizations.services import required_role
from django.db import transaction
from django.core.exceptions import ValidationError,PermissionDenied
from django.utils import timezone
from organizations.services import PERMISSIONS


COMMITTED_STATUSES = [SpendingReq.Status.APPROVED, SpendingReq.Status.SUBMITTED]

def approved_spend(org): #total of all approved spend or if its submitted then that amount
    commited = Case(
        #when is like a if statement
        When(status = SpendingReq.Status.APPROVED, then= F("spend")), #F("spend") means the value inside of this rows spend column
        When(status = SpendingReq.Status.SUBMITTED, then= F("reimamount")), 
        #default is like else
        default = Decimal("0"), #if its not approved/submitted then its 0
        output_field = DecimalField(max_digits = 10, decimal_places = 2) 
    )
    return (SpendingReq.objects
            .filter(organization = org, status__in =COMMITTED_STATUSES)
            .aggregate(total=Coalesce(Sum(commited), Decimal("0")))["total"]) 

def pending_reim(org): #exclusively non completed reimbursement
    pending = Case(
        When(status = SpendingReq.Status.SUBMITTED, then= F("reimamount")),
        default = Decimal("0"),
        output_field = DecimalField(max_digits = 10, decimal_places = 2)
    )
    return (SpendingReq.objects
            .filter(organization = org, status__in = COMMITTED_STATUSES)
            .aggregate(total= Coalesce(Sum(pending), Decimal("0")))["total"])

def pending_approved(org): #exclusively approved
    pending = Case(
        When(status = SpendingReq.Status.APPROVED, then= F("spend")),
        default = Decimal("0"),
        output_field = DecimalField(max_digits = 10, decimal_places = 2)
    )
    return (SpendingReq.objects
            .filter(organization = org, status__in = COMMITTED_STATUSES)
            .aggregate(total= Coalesce(Sum(pending), Decimal("0")))["total"])

def true_bal(org):
    return (LedgerEntry.objects
    .filter(organization=org)
    .aggregate(
        total=Coalesce(
            Sum("cost"),
            Decimal("0"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )["total"]
) 

def org_fin_view(*, actor, org):
    required_role(actor, org, PERMISSIONS["view.requests.org"])
    real = true_bal(org)
    pendreim = pending_reim(org) #exclusively pending reimbursements
    pendapp = pending_approved(org) #exclusively pending approvals

    approved = approved_spend(org) #total of all approved spend (approved reqs and submitted reimbursement)

    working = real - approved

    return {"true_balance": real,"pending_reim": pendreim, "curr_approved": approved, "pending_approved": pendapp, "working_balance": working}

@transaction.atomic
def bal_adjustment(*, actor, org, adjustment, title):
    required_role(actor, org, PERMISSIONS["bal.adjustment"])
    Organization.objects.select_for_update().get(pk = org.pk)
    if adjustment == 0:
        raise ValidationError("Adjustment cannot be 0") 
    entry = LedgerEntry(
            organization = org,
            done_by = actor,
            cost = adjustment,
            title = title,
        )
    entry.full_clean()
    entry.save()
    return entry

BALANCE_ADJUSTMENT_TITLE = "Balance Reconciliation"
@transaction.atomic
def set_bal(*, actor, org, target):
    required_role(actor, org, PERMISSIONS["bal.adjustment"])
    Organization.objects.select_for_update().get(pk = org.pk)
    real = true_bal(org)
    entry = LedgerEntry(
            organization = org,
            done_by = actor,
            cost = target-real,
            title = BALANCE_ADJUSTMENT_TITLE,
    )
    entry.full_clean()
    entry.save()
    return entry

#UPDATEDDDDDDD
@transaction.atomic #makes sure the ledger and status change move together
def request_complete(*, actor, request_id, org):
    required_role(actor, org, PERMISSIONS["request.complete"])
    Organization.objects.select_for_update().get(pk = org.pk)
    try: 
        req = (SpendingReq.objects
           .select_for_update(of=("self",)) #locks the row so no one can change it
           .get(pk = request_id, organization = org))
    except SpendingReq.DoesNotExist:
        raise PermissionDenied
    if req.status != SpendingReq.Status.SUBMITTED:
        raise ValidationError("Only submitted requests can be completed")
    if req.reimamount is None or req.reimamount <= 0:
        raise ValidationError("Reimbursement amount must be positive")
    
    req.status = SpendingReq.Status.COMPLETED
    req.completed_at = timezone.now()
    req.completed_by = actor
    req.save(update_fields=["status", "completed_at", "completed_by"])

    #creates the ledger entry
    entry = LedgerEntry(
        organization = org,
        done_by = actor,
        spending_req = req,
        cost = -req.reimamount,
        title = req.title,
    )
    entry.full_clean()
    entry.save()
    return entry


@transaction.atomic
def request_approve(*, actor, request_id, org):
    required_role(actor, org, PERMISSIONS["request.accept"])
    try:
        req = (SpendingReq.objects
                .select_for_update(of=("self",))  #locks the row so one one can change it
                .get(pk = request_id, organization = org))
    except SpendingReq.DoesNotExist:
            raise PermissionDenied
    if req.status != SpendingReq.Status.PENDING:
            raise ValidationError("Only pending requests can be accepted")
    req.status = SpendingReq.Status.APPROVED
    req.reviewed_by = actor
    req.reviewed_at = timezone.now()
    req.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return req

@transaction.atomic
def request_deny(*, actor, request_id, org):
    required_role(actor, org, PERMISSIONS["request.deny"])
    try:
        req = (SpendingReq.objects
                .select_for_update(of=("self",))  #locks the row so one one can change it
                .get(pk = request_id, organization = org))
    except SpendingReq.DoesNotExist:
            raise PermissionDenied
    if req.status != SpendingReq.Status.PENDING:
            raise ValidationError("Only pending requests can be denied")
    req.status = SpendingReq.Status.DENIED
    req.reviewed_by = actor
    req.reviewed_at = timezone.now()
    req.save(update_fields=["status", "reviewed_by" , "reviewed_at"])
    return req

@transaction.atomic
def request_spending(*, actor, org, title, spend):
    required_role(actor, org, PERMISSIONS["request.submit"])
    entry = SpendingReq(
        organization = org,
        title = title,
        spend = spend,
        requested_by = actor,
    )
    entry.full_clean()
    entry.save()
    return entry


@transaction.atomic
def request_reim(*, actor, request_id, org, reimamount):
    required_role(actor, org, PERMISSIONS["request.submit"])
    try:
        req = (SpendingReq.objects
                .select_for_update(of=("self",))  #locks the row so one one can change it
                .get(pk = request_id, requested_by=actor, organization = org))
    except SpendingReq.DoesNotExist:
            raise PermissionDenied
    if req.status == SpendingReq.Status.SUBMITTED or req.status == SpendingReq.Status.COMPLETED:
                raise ValidationError("Already submitted or completed")
    if req.status != SpendingReq.Status.APPROVED:
            raise ValidationError("Only approved requests can submit for reimbursement")
    if reimamount is None or reimamount <= 0:
            raise ValidationError("Reimbursement amount must be positive")
    
    req.over_budget = reimamount > req.spend + org.overspend_limit
    req.status = SpendingReq.Status.SUBMITTED
    req.reimamount = reimamount
    req.save(update_fields=["status", "reimamount", "over_budget"])
    return req

def get_own_request(*, actor, org, request_id):
    required_role(actor, org, PERMISSIONS["view.requests.personal"])
    try:
        spending_req = SpendingReq.objects.get(requested_by = actor, organization = org, pk = request_id)
    except SpendingReq.DoesNotExist:
            raise PermissionDenied
    return spending_req

#need to build view org requests, view personal requests, deny request

def list_requests(*, actor, org, status):
    required_role(actor, org, PERMISSIONS["view.requests.org"])       # enforcement, same as your services
    spending_reqs = SpendingReq.objects.filter(organization=org)         # org scoping first, always
    if status != "all":
        spending_reqs = spending_reqs.filter(status=status)
    return spending_reqs.select_related("requested_by").order_by("-created_at")

def list_personal(*, actor, org, status):
    required_role(actor, org, PERMISSIONS["view.requests.personal"])
    spending_reqs = SpendingReq.objects.filter(requested_by = actor, organization = org)
    if status != "all":
        spending_reqs = spending_reqs.filter(status=status)
    pending_count = SpendingReq.objects.filter(requested_by = actor, organization=org, status=SpendingReq.Status.PENDING).count()
    submitted_count = SpendingReq.objects.filter(requested_by = actor, organization=org, status=SpendingReq.Status.SUBMITTED).count()
    return {"spending_reqs" :spending_reqs.order_by("-created_at"), "pending_count": pending_count, "submitted_count": submitted_count}

def ledger_list(*, actor, org):
    required_role(actor, org, PERMISSIONS["view.ledger"])
    ledgers = LedgerEntry.objects.filter(organization = org)
    return ledgers.select_related("done_by").order_by("-created_at")
    