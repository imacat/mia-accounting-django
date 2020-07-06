from django.contrib.auth import logout as logout_user
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST, require_GET


@require_GET
def home(request):
    """The view of the home page.

    Args:
        request (HttpRequest): The request.

    Returns:
        HttpRedirectResponse: The redirect response.
    """
    return render(request, "index.html")


@require_POST
def logout(request):
    """The view to log out a user.

    Args:
        request (HttpRequest): The request.

    Returns:
        HttpRedirectResponse: The redirect response.
    """
    logout_user(request)
    if "next" in request.POST:
        request.session["logout"] = True
        return redirect(request.POST["next"])
    return redirect("/")
