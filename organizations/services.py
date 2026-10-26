from django.core.exceptions import PermissionDenied
from organizations.models import Membership
from django.db import transaction, IntegrityError
from django.utils.text import slugify
from django.core.exceptions import ValidationError,PermissionDenied
from organizations.models import Organization, Membership


def get_role(user, org):
    if not user.is_authenticated:
        return None
    return (Membership.objects.filter(user=user, organization = org).values_list("role", flat = True).first()) 

def required_role(user, org, allowed_roles):
    if get_role(user,org) not in allowed_roles:
        raise PermissionDenied
    
def get_memberships(*, actor):
    return Membership.objects.filter(user=actor).select_related("organization")

@transaction.atomic 
def create_org(*, actor, name):
    slug = slugify(name)
    if not slug:
        raise ValidationError("Name must contain at least one letter or number")
    if Organization.objects.filter(slug=slug).exists():
        raise ValidationError("An org with that name exists already")
    org = Organization(name = name, slug= slug)
    org.full_clean()
    try:
        org.save()
    except IntegrityError:
        raise ValidationError("An org with that name exists already")
    Membership.objects.create(user = actor, organization = org, role = Membership.Role.PRESIDENT)
    return org