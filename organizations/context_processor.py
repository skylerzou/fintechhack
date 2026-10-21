def current_org(request):
    return {"current_org": getattr(request, "organization", None)}