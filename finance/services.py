from decimal import Decimal
from django.db.models import Sum, When, F, Case, DecimalField
from .models import SpendingReq, LedgerEntry
from django.db.models.functions import Coalesce
from organizations.models import Membership
from organizations.services import required_role
from django.db import transaction
from django.core.exceptions import ValidationError,PermissionDenied


COMMITTED_STATUSES = [SpendingReq.Status.APPROVED, SpendingReq.Status.SUBMITTED]
R = Membership.Role
PERMISSIONS = {
    "request.submit": (R.MEMBER, R.PRESIDENT),
    "request.accept": (R.TREASURER),
    "request.complete": {R.TREASURER},
    "request.deny":{R.TREASURER},
    "view.requests.org": {R.TREASURER, R.PRESIDENT},
    "view.requests.personal": {R.MEMBER, R.PRESIDENT},

}
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
    pendreim = pending_reim(org)
    approved = approved_spend(org)
    return {"true_balance": real,"pending_reim": pendreim, "curr_approved": approved}


#UPDATEDDDDDDD
@transaction.atomic #makes sure the ledger and status change move together
def request_complete(*, actor, request_id, org):
    required_role(actor, org, PERMISSIONS["request.complete"])
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
    req.save(update_fields=["status"])

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
    req.save(update_fields=["status"])
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
    req.save(update_fields=["status"])
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
    # TODO: overspend limit check
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
    req.status = SpendingReq.Status.SUBMITTED
    req.reimamount = reimamount
    req.save(update_fields=["status", "reimamount"])
    return req

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
    