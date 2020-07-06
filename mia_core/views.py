from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


@require_POST
def logout_view(request):
    """The view to log out a user.

    Args:
        request (HttpRequest): The request.

    Returns:
        HttpRedirectResponse: The redirect response.
    """
    logout(request)
    if "next" in request.POST:
        request.session["logout"] = True
        return redirect(request.POST["next"])
    return redirect("/")
