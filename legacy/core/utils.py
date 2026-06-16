"""
Utility functions for the core application.
"""


def get_site_domain(request):
    """
    Get the full site domain (including protocol) from the request.

    Args:
        request: Django HttpRequest object

    Returns:
        str: Full site domain with protocol
            (e.g., 'https://bildungsplattform.rauchfangkehrer.or.at')
    """
    if request:
        protocol = "https" if request.is_secure() else "http"
        host = request.get_host()
        return f"{protocol}://{host}"

    # Fallback to default domain if no request available
    return "https://bildungsplattform.rauchfangkehrer.or.at"
