from django.db import models
from django.conf import settings
# Create your models here.


class Organization(models.Model):
    name = models.CharField(max_length=200)

class Membership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        TREASURER = "treasurer", "Treasurer"
        PRESIDENT = "president", "President"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete= models.CASCADE, related_name = "memberships")
    role = models.CharField(max_length = 20, choices = Role.choices, default = Role.MEMBER)

    class Meta:
        #basically the same user cant be in the same club multiple times
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"],
                name="unique_user_org_membership",
            ),
             models.CheckConstraint(
                condition=models.Q(role__in=["member", "treasurer", "president"]),
                name="valid_membership_role",
            ),
    ]