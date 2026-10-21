from django.db import models
from django.conf import settings
# Create your models here.


class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique= True, blank = False)

class Membership(models.Model):
    #again these are the choices for lower case role
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        TREASURER = "treasurer", "Treasurer"
        PRESIDENT = "president", "President"

    #settings.AUTH_USER_MODEL just links to the auth user model linked to in settings avoids circlular imports from User
    #on_delete is CASCADE here because membership has no meaning if the user or org is gone
    #say user 5 is a member of org 2, but they delete their account. Now the membership row says NA belongs to the org, this is useless
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name="membership")
    organization = models.ForeignKey(Organization, on_delete= models.CASCADE, related_name = "membership")
    role = models.CharField(max_length = 20, choices = Role.choices, default = Role.MEMBER)

    class Meta:
        # the same user cant be in the same club multiple times
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"],
                name="unique_user_org_membership",
            ),
            # role must be "member", "treasurer", or "president"
            # hardcoded so technically bad practice
            models.CheckConstraint(
                condition=models.Q(role__in=["member", "treasurer", "president"]),
                name="valid_membership_role",
            ),
    ]