def current_org(request):
    return {"current_org": getattr(request, "org", None)}

def current_role(request):
    return {"current_role": getattr(request, "role", None)}