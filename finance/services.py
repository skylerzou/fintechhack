from decimal import Decimal
from django.db.models import Sum, When, F, Case, DecimalField
from .models import SpendingReq, LedgerEntry
from django.db.models.functions import Coalesce
from organizations.models import Membership
from organizations.services import required_role
from django.db import transaction
from django.core.exceptions import ValidationError


COMMITTED_STATUSES = [SpendingReq.Status.APPROVED, SpendingReq.Status.SUBMITTED]
R = Membership.Role
PERMISSIONS = {
    "request.submit": (R.MEMBER, R.PRESIDENT),
    "request.accept": (R.TREASURER),
    "request.complete": {R.TREASURER},

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

@transaction.atomic #makes sure the ledger and status change move together
def complete_req(*, actor, request_id):
    req = (SpendingReq.objects
           .select_for_update(of=("self",)) #locks the row so one one can change it
           .select_related("organization")
           .get(pk = request_id))
    
    required_role(actor, req.organization, PERMISSIONS["request.complete"])
    if req.status != SpendingReq.Status.SUBMITTED:
        raise ValidationError("Only submitted requests can be completed")
    if req.reimamount < 0:
        raise ValidationError("Reimbursement amount must positive")
    
    req.status = SpendingReq.Status.COMPLETED
    req.save(update_fields=["status"])

    #creates the ledger entry
    entry = LedgerEntry.objects.create(
        organization = req.organization,
        done_by = actor,
        spending_req = req,
        cost = -req.reimamount,
        title = req.title,
    )
    entry.full_clean()
    entry.save()
    return entry


@transaction.atomic
def accept_req(*, actor, request_id):
    req = (SpendingReq.objects
            .select_for_update(of=("self",))  #locks the row so one one can change it
            .select_related("organization")
            .get(pk = request_id))
    required_role(actor, req.organization, PERMISSIONS["request.accept"])
    if req.status != SpendingReq.Status.PENDING:
            raise ValidationError("Only pending requests can be accepted")
    req.status = SpendingReq.Status.ACCEPTED
    req.save(update_fields=["status"])
    return req

@transaction.atomic
def request_spending(*, actor, org, name, spend):
    required_role(actor, org, PERMISSIONS["request.submit"])
    entry = SpendingReq.objects.create(
        organization = org,
        title = name,
        spend = spend,
        requestedby = actor,
    )
    entry.full_clean()
    entry.save()
    return entry