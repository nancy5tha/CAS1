from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.role == "Admin":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.role == "Teacher":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
