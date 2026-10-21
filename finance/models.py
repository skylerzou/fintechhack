from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.conf import settings

# Create your models here.
class SpendingReq(models.Model):

    #the choices for status
    class Status(models.TextChoices):
            PENDING = "pending", "Awaiting Review" #first is database second is displayed/lable
            APPROVED = "approved", "Request Approved"
            DENIED = "denied", "Request Denied"
            SUBMITTED = "submitted", "Reimbursement Submitted"
            COMPLETED = "completed", "Completed Request"

    #ForeignKey links to another model in this organization.Organization (which is just a name)
    #we have on_delete to PROTECT which prevents org from being deleted so long as it has at least 1 spending request
    organization = models.ForeignKey("organizations.Organization", on_delete= models.PROTECT, related_name = "spending_requests")
    title = models.CharField(max_length=200)
    #must have max_digits, the validators ensures the field only accepts values > 0.01
    spend = models.DecimalField(max_digits = 10,decimal_places=2,validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length = 20, choices = Status.choices, default = Status.PENDING)
    reimamount = models.DecimalField(max_digits = 10,decimal_places=2, null=True, blank=True,validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add = True)
    

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.PROTECT, related_name = "spending_request")
    #null = TRUE, blank = TRUE because the field is optional, null is spending request not approved yet, blank = true allows submission without the field filled out
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, blank=True,  on_delete = models.PROTECT, related_name = "approved_spending_requests")
    completed_by= models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete = models.PROTECT, related_name = "completed_spending_requests")

    class Meta:
        constraints = [
            models.CheckConstraint(condition = Q(reimamount__isnull= True) | Q(reimamount__gte = Decimal("0.01")), name = "spendingreq_reimamount_gte_0_01"), #reim can either be null or > .01
            models.CheckConstraint(condition = Q(spend__gte = Decimal("0.01")), name = "spendingreq_spend_gte_0_01"), #spend must be > .01
        ]

class LedgerEntry(models.Model):
    #related name creates a reverse relationship: all ledgers by an org is org.ledger_entry.all()
    organization = models.ForeignKey("organizations.Organization", on_delete= models.PROTECT, related_name = "ledger_entry")
    done_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.PROTECT, related_name = "ledger_entry")
    created_at = models.DateTimeField(auto_now_add = True)
    spending_req = models.OneToOneField(SpendingReq, null = True, blank = True, on_delete = models.PROTECT, related_name = "ledger_entry")
    cost = models.DecimalField(max_digits = 10, decimal_places= 2) #we dont have the min value validation here because it should be possible to subtract from the ledger via spending requests or adjustment
    title = models.CharField(max_length = 200)

    class Meta:
        constraints = [
            models.CheckConstraint(condition = ~Q(cost = 0), name = "ledger_cost_nonzero"),  # ~ means ! so a ledger entry must not be 0  
            models.CheckConstraint(condition = Q(spending_req__isnull= True) | Q(cost__lt = 0), name = "spending_ledger_cost_negative"),
            #if its not a spending request or the cost > 0 then reject ie: if its spending request and cost >0 then reject
            #aka if its a spending req and its adding money then its rejected from the ledger
        ]