from decimal import Decimal
from django.db.models import Sum, When, F, Case, DecimalField
from .models import SpendingReq
from django.db.models.functions import Coalesce


COMMITTED_STATUSES = [SpendingReq.Status.APPROVED, SpendingReq.Status.SUBMITTED]
def approved_spend(org): #total of all approved spend or if its submitted then that amount
    commited = Case(
        When(status = SpendingReq.Status.APPROVED, then= F("spend")), #F("spend") means the value inside of this rows spend column
        When(status = SpendingReq.Status.SUBMITTED, then= F("reimamount")), 
        default = Decimal("0"), #if its not approved/submitted then its 0
        output_field = DecimalField(max_digits = 10, decimal_places = 2)
    )
    return (SpendingReq.objects.filter(organization = org, status_in =COMMITTED_STATUSES).aggregate(total=Coalesce(Sum(commited), Decimal("0")))["total"]) 

def pending_reim(org): #exclusively none completed reimbursement
    commited = Case(
        When(status = SpendingReq.Status.SUBMITTED, then= F("reimamount")),
        default = Decimal("0"),
        output_field = DecimalField(max_digits = 10, decimal_places = 2)
    )
    return (SpendingReq.objects.filter(organization = org, status_in = COMMITTED_STATUSES).aggregate(total= Coalesce(Sum(commited), Decimal("0")))["total"])

def working_bal(org):
    pass