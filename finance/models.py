from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import Q

# Create your models here.
class SpendingReq(models.Model):
    class Status(models.TextChoices):
            PENDING = "pending", "Awaiting Review" #first is database second is displayed/lable
            APPROVED = "approved", "Request Approved"
            DENIED = "denied", "Request Denied"
            SUBMITTED = "submitted", "Reimbursement Submitted"
            COMPLETED = "completed", "Completed Request"

    organization = models.ForeignKey("organizations.Organization", on_delete= models.PROTECT, related_name = "spending_requests")
    title = models.CharField(max_length=200)
    spend = models.DecimalField(max_digits = 10,decimal_places=2,validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length = 20, choices = Status.choices, default = Status.PENDING)
    reimamount = models.DecimalField(max_digits = 10,decimal_places=2, default=Decimal('0.00'))

    requestedby = models.ForeignKey("users.User", on_delete = models.PROTECT, related_name = "spending_request")
    approved_by = models.ForeignKey("users.User",null=True, blank=True,  on_delete = models.PROTECT, related_name = "approved_spending_requests")
    completed_by= models.ForeignKey("users.User", null=True, blank=True, on_delete = models.PROTECT, related_name = "completed_spending_requests")

class LedgerEntry(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete= models.PROTECT, related_name = "ledger_entry")
    done_by = models.ForeignKey("users.User", on_delete = models.PROTECT, related_name = "ledger_entry")
    created_at = models.DateTimeField(auto_now_add = True)
    spending_req = models.OneToOneField(SpendingReq, null = True, blank = True, on_delete = models.PROTECT, related_name = "ledger_entry")
    cost = models.DecimalField(max_digits = 10, decimal_places= 2)
    title = models.CharField(max_length = 200)

    class Meta:
        constraints = [
            models.CheckConstraint(condition = ~Q(cost = 0), name = "ledger_cost_nonzero"),  # ~ means ! so a ledger must not be 0  
            models.CheckConstraint(condition = Q(spending_requests_isnull= True) | Q(cost__lt = 0), name = "ledger_cost_negative"),
        ]
