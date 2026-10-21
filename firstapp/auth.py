"""Access control: which logged-in roles may open which pages."""
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import redirect

POLICE_ROLES = ('inspector', 'officer', 'police')

# Where each role lands when it opens a page that is not meant for it
ROLE_HOME = {
    'citizen': 'citizen_dashboard',
    'inspector': 'inspector_dashboard',
    'officer': 'officer_dashboard',
    'police': 'officer_dashboard',
    'admin': 'admin_dashboard',
}


def role_required(*roles, json=False):
    """Only logged-in users may open the view; with `roles`, only users with one of those roles.

    Visitors who are not logged in go to the login page. Logged-in users with the wrong role go
    back to their own dashboard. With json=True (fetch/AJAX endpoints) a JSON error is returned instead.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                if json:
                    return JsonResponse({'status': 'error', 'message': 'Please log in again.'}, status=401)
                return redirect('login')
            if roles and user.get('role') not in roles:
                if json:
                    return JsonResponse({'status': 'error', 'message': 'Not allowed for your account.'}, status=403)
                return redirect(ROLE_HOME.get(user.get('role'), 'login'))
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
