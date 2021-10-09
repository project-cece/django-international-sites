from django.utils.deprecation import MiddlewareMixin
from django.utils import translation
from django.conf import settings

from .models import CountrySite


class InternationalSiteMiddleware(MiddlewareMixin):
    """
    Middleware that sets `country` attribute to request object.
    """

    def process_request(self, request):
        request.country_site = CountrySite.objects.get_current(request)

        # Set language based on country site if wanted
        if (getattr(settings, "FORCE_COUNTRY_LANGUAGE", False)):
            default_language = request.country_site.default_language
            if request.LANGUAGE_CODE != default_language:
                translation.activate(default_language)
                request.LANGUAGE_CODE = translation.get_language()


    def process_response(self, request, response):
        local = request.COOKIES.get("local", "")
        country_code = request.country_site.country_code

        # For use by js frontend
        if local != country_code:
            response.set_cookie("local", country_code)
            request.session["local"] = country_code

        return response
