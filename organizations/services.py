from django.core.exceptions import PermissionDenied
from organizations.models import Membership

def get_role(user, org):
    if not user.is_authenticated:
        return None
    return (Membership.objects.filter(user=user, organization = org).values_list("role", flat = True).first()) 

def required_role(user, org, allowed_roles):
    if get_role(user,org) not in allowed_roles:
        raise PermissionDenied


    