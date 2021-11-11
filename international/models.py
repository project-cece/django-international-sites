from django.db import models
from django.conf import settings
from django.http.request import split_domain_port
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import pre_delete, pre_save
from django.core.files.storage import FileSystemStorage

# from django.contrib.gis.geoip2 import GeoIP2
# from django.core.validators import URLValidator

from .localize import get_country_from_ip

# Similar to Sites cache https://github.com/django/django/blob/main/django/contrib/sites/models.py
COUNTRY_SITE_CACHE = {}

STATIC_STORAGE = FileSystemStorage(location=settings.STATIC_ROOT)

class CountrySiteManager(models.Manager):
    use_in_migrations = True

    def active_sites(self):
        return self.get_queryset().filter(active=True)

    def _get_site_by_country_code(self, country_code):
        if country_code not in COUNTRY_SITE_CACHE:
            site = self.get(country_code=country_code)
            SITE_CACHE[country_code] = site
        return SITE_CACHE[country_code]

    def _get_country_site_by_request(self, request):
        host = request.get_host()

        country_code = None

        try:
            # For unique domain names, map to countrycode without db
            uniques = getattr(settings, "UNIQUE_DOMAINS", {})
            if host in uniques:
                country_code = uniques[host]

            # For GET requests on generic .com domain, check if url parameter is used to force locale
            elif request.method == "GET" and request.GET.get("c"):
                country_code = request.GET["c"].upper()

            # Check if user already has location saved in cookie
            elif request.COOKIES.get("local", False):
                # country_code = request.session.get("local")
                country_code = request.COOKIES.get("local")

            # TODO: If none of the above: Detect location based on IP
            elif getattr(settings, "GEOIP_REDIRECT", False):
                country_code = get_country_from_ip(request)

                if settings.DEBUG:
                    print("Detected country code from IP: {0}".format(country_code))

            if not country_code:
                country_code = getattr(settings, "DEFAULT_COUNTRY_CODE", '')

            # First attempt to look up the site by host with or without port.
            if country_code not in COUNTRY_SITE_CACHE:
                country_site = self.get(country_code=country_code)
                COUNTRY_SITE_CACHE[country_code] = country_site

            return COUNTRY_SITE_CACHE[country_code]

        except CountrySite.DoesNotExist:

            # Fallback to looking up site after stripping port from the host.
            if settings.DEBUG:
                domain, port = split_domain_port(host)
                print(domain)
                print(port)
                if port in getattr(settings, "DEBUG_UNIQUE_DOMAINS", {}):
                    country_code = settings.DEBUG_UNIQUE_DOMAINS[port]
                    print(country_code)
                    COUNTRY_SITE_CACHE[country_code] = self.get(country_code=country_code)

                    return COUNTRY_SITE_CACHE[country_code]

            country_code = getattr(settings, "DEFAULT_COUNTRY_CODE", "")
            if country_code:
                COUNTRY_SITE_CACHE[country_code] = self.get(country_code=country_code)
                return COUNTRY_SITE_CACHE[country_code]

            raise ImproperlyConfigured(
                "You're using the \"international\" app without having "
                "set the DEFAULT_COUNTRY_CODE setting. Create a country site "
                "in your database and set the DEFAULT_COUNTRY_CODE setting "
                "to fix this error."
            )

    def get_current(self, request=None, country_code=None):
        """
        Return the current CountrySite on the DEFAULT_COUNTRY_CODE in the project's settings.
        If DEFAULT_COUNTRY_CODE isn't defined, return the site with domain matching
        request.get_host(). The ``CountrySite`` object is cached the first time it's
        retrieved from the database.
        """
        from django.conf import settings

        if country_code:
            return self._get_site_by_country_code(country_code)
        elif request:
            return self._get_country_site_by_request(request)
        elif getattr(settings, 'DEFAULT_COUNTRY_CODE', ''):
            country_code = settings.DEFAULT_COUNTRY_CODE
            return self._get_site_by_country_code(country_code)
        raise ImproperlyConfigured(
            "You're using the \"international\" app without having "
            "set the DEFAULT_COUNTRY_CODE setting. Create a country site "
            "in your database and set the DEFAULT_COUNTRY_CODE setting "
            "to fix this error."
        )

    def clear_cache(self):
        """Clear the ``CountrySite`` object cache."""
        global COUNTRY_SITE_CACHE
        COUNTRY_SITE_CACHE = {}

    # def get_by_natural_key(self, country_code):
    #     return self.get(country_code=country_code)


class CountrySite(models.Model):

    domain = models.CharField(
        'Domain name',
        max_length=100,
    )
    name = models.CharField('Display name', max_length=50)
    country_code = models.SlugField(
        max_length=10, 
        help_text="Unique country code (e.g. NL, UK, DE)", 
        unique=True
    )
    active = models.BooleanField(default=True)

    # See: https://docs.djangoproject.com/en/3.2/topics/i18n/
    default_language = models.CharField(
        max_length=25, #choices=settings.LANGUAGES,
        help_text="Default language to be displayed on this country site")

    # icon = models.ImageField(
    #     upload_to=getattr(settings, "SITE_ICON_PATH", "site_icons/"), 
    #     storage=getattr(settings, "SITE_ICON_STORAGE", STATIC_STORAGE), blank=True, null=True) 

    objects = CountrySiteManager()

    class Meta:
        # db_table = 'django_site'
        verbose_name = 'Country Site'
        verbose_name_plural = 'Country Sites'
        ordering = ['domain']

    def save(self, *args, **kwargs):
        self.country_code = self.country_code.upper()
        return super(CountrySite, self).save(*args, **kwargs)

    def __str__(self):
        return self.country_code

    def get_default_language_display(self):
        return dict(settings.LANGUAGES).get(self.default_language)

    def get_icon(self):
        if getattr(settings, "SITE_ICON_DIR", False):
            return settings.SITE_ICON_DIR + self.country_code + getattr(settings, "SITE_ICON_EXT", ".png")
        return ""

    def get_country_site_switch_url(self):

        unique = getattr(settings, "UNIQUE_DOMAINS", {})
        if getattr(unique, self.domain, False):
            return self.domain 

        return "//" + self.domain + "?c={0}".format(self.country_code)


    # def natural_key(self):
    #     return (self.country_code,)


class InternationalModelManager(models.Manager):

    def by_country(self, country_code):
        """
        Return only objects that are linked to this country code
        """
        if not getattr(settings, "INTERNATIONAL_APP", True):
            return self.get_queryset()

        return self.get_queryset().filter(country_sites__country_code=country_code)
        

    def by_language(self, language_code):
        """
        Return only objects that are tagged with this language code
        """
        if not getattr(settings, "INTERNATIONAL_APP", True):
            return self.get_queryset()
        
        return self.get_queryset().filter(object_language=language_code)


class InternationalModel(models.Model):
    """
    Base model to be inherated in objects that should be associated
    with particular country site(s) and/or keeping track of languages
    """

    country_sites = models.ManyToManyField("international.CountrySite", blank=True)
    object_language = models.CharField(
        'Language',
        max_length=25, null=True, blank=True,
        help_text="The language used for this item")

    # Extend default object manager
    objects = InternationalModelManager()

    class Meta:
        abstract = True


def clear_country_site_cache(sender, **kwargs):
    """
    Clear the cache (if primed) each time a country site is saved or deleted.
    """
    instance = kwargs['instance']
    using = kwargs['using']
    try:
        del COUNTRY_SITE_CACHE[CountrySite.objects.using(using).get(pk=instance.pk).country_code]
    except (KeyError, CountrySite.DoesNotExist):
        pass


pre_save.connect(clear_country_site_cache, sender=CountrySite)
pre_delete.connect(clear_country_site_cache, sender=CountrySite)