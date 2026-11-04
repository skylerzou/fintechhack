from django.core.exceptions import PermissionDenied
from organizations.models import Membership
from django.db import transaction, IntegrityError
from django.utils.text import slugify
from django.core.exceptions import ValidationError,PermissionDenied
from organizations.models import Organization, Membership,ROLE_RANK, generate_join_code

R = Membership.Role
PERMISSIONS = {
    "request.submit": (R.MEMBER, R.TREASURER, R.PRESIDENT),
    "request.accept": (R.TREASURER),
    "request.complete": {R.TREASURER},
    "request.deny":{R.TREASURER},
    "view.requests.org": {R.TREASURER, R.PRESIDENT},
    "view.requests.personal": {R.MEMBER, R.TREASURER, R.PRESIDENT},
    "org.admin" : {R.PRESIDENT},
    "bal.adjustment" : {R.TREASURER, R.PRESIDENT},
    "overspend.adjustment" : {R.TREASURER, R.PRESIDENT},
    "view.ledger": {R.TREASURER, R.PRESIDENT},
}

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


def regen_join_code(*, actor, org):
    required_role(user = actor, org = org, allowed_roles = PERMISSIONS["org.admin"])
    org.join_code= generate_join_code()
    org.save(update_fields=["join_code"])
    return org

def join_org(*, actor, code):
    code = code.strip().upper()

    try:
        org = Organization.objects.get(join_code = code)
    except Organization.DoesNotExist:
            raise ValidationError("Invalid join code")
    
    if Membership.objects.filter(organization = org, user = actor).exists():
        raise ValidationError("Already in this org")
    try:
        Membership.objects.create(user = actor, organization = org)
    except IntegrityError:
        raise ValidationError("Already in this org")
    return org

def get_org_admin(*, actor, org):
    required_role(user = actor, org = org, allowed_roles = PERMISSIONS["org.admin"])
    memberships = (Membership.objects
               .filter(organization=org)
               .select_related("user")
               .annotate(rank=ROLE_RANK)
               .order_by("rank", "user__last_name", "user__first_name"))
    return {"memberships": memberships, "join_code": org.join_code}

def change_role(*, actor, membership_id, org, new_role):
    required_role(user = actor, org = org, allowed_roles = PERMISSIONS["org.admin"])
    if new_role not in [R.MEMBER, R.TREASURER]:
        raise ValidationError("Invalid role")
    try:
        membership = Membership.objects.get(organization=org, pk=membership_id)
    except Membership.DoesNotExist:
        raise PermissionDenied
    if membership.role == R.PRESIDENT:
        raise ValidationError("Cannot change president role without transfer")
    membership.role = new_role
    membership.save(update_fields=["role"])
    return membership


def overspend_adjustment(*, actor, org, new_limit):
    required_role(user = actor, org = org, allowed_roles = PERMISSIONS["overspend.adjustment"])
    if new_limit is None or new_limit < 0:
        raise ValidationError("Must be positive")
    org.overspend_limit = new_limit
    org.save(update_fields=["overspend_limit"])
    return org
        