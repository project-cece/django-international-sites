import datetime
from django.utils.deprecation import MiddlewareMixin
from django.utils import translation
from django.conf import settings
from django.utils import timezone 
from .models import CountrySite
from .views import get_country_data_from_request

def is_crawler_request(request):
    """
    Very basic crawler detection using user agent
    """

    user_agent = request.META.get("HTTP_USER_AGENT")
    if user_agent:
        if "bot" in user_agent.lower():
            return True 

        if "spider" in user_agent.lower():
            return True

    return False

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

        # Detect location if not know already
        if not getattr(settings, "GEOIP_REDIRECT", False):
            if not request.COOKIES.get("local_dc", ""):

                # Skip location detection for known crawlers
                if not is_crawler_request(request):
                    detection = get_country_data_from_request(request)
                    detected_country_code = {"GB": "UK"}.get(detection["country"], detection["country"])
                else:
                    # For crawlers use value of current country site
                    detected_country_code = country_code

                expires = timezone.now() + timezone.timedelta(days=2)
                expires = datetime.datetime.strftime(expires, "%a, %d-%b-%Y %H:%M:%S GMT")

                if not detected_country_code:
                    detected_country_code = settings.DEFAULT_COUNTRY_CODE
                    
                response.set_cookie("local_dc", detected_country_code, expires=expires)

        return response
