from django.contrib.auth.views import redirect_to_login
from services import get_role
from organizations.models import Membership
from django.http import Http404

class OrgMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        slug = view_kwargs.get("organization_slug")
        if slug is None:
            return None  
        
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        
        membership = (
        Membership.objects
        .select_related("organization")
        .filter(user=request.user, organization__slug=slug)
        .first()
    )
        if membership is None:
            raise Http404
        
        request.org = membership.organization
        request.role = membership.role

        return None
        