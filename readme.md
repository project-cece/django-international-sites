# Django International 

An app to allow a single Django application to serve multiple domains and country sites and adjust the content based on that. Similar to the Django Sites Framework, but without the `Site` hardcoded in the settings of the app. Instead it uses a `CountrySite` object (similar to `Site`) which can be set dynamically in the middleware based on the request domain, session, url parameter or visitor location. 

## Install

- `pip install django-international-sites`
- Add "international" to `INSTALLED_APPS` in `settings.py`
- Run `python manage.py migrate international`
- Add `CountrySite` objects in admin `/admin/international/countrysite/`

## Settings

```python
# Fallback country code
DEFAULT_COUNTRY_CODE = "NL"

# Optional: Set the below if you want the middleware to set the current site based
# on the location/country deduced from the visitor IP
# When using international.middleware.InternationalSiteMiddleware obtain
# geoip license key (for free) at xx and set path were geoip2 country library is
# to be installed here
GEOIP_PATH = os.path.join("geoip")
GEOIP_LICENSE = "asecretkeybymaxmind"

# Map domains uniquely to a single country code (optional)
UNIQUE_DOMAINS = {"example.nl": "nl", "example.co.uk": "uk"}

# Directory for site icons to be displayed in admin (optional)
SITE_ICON_DIR = "static/site_icons/"
```

## Request middleware

How is the country code detected from the request?

1. If a unique domain name set in `settings.UNIQUE_DOMAINS` (e.g. example.nl), use country data of related country code
2. If country code is forced as url parameter (i.e. example.com/c=fr), use that country code
3. If a cookie with location preference is used, use that country code
4. Check location based on visitor IP address, use that country code
5. If nothing could be detected, use default country code

Add the middleware to settings _after_ the Django `LocaleMiddleware`:

```python
MIDDLEWARE = [
	...
    'django.middleware.locale.LocaleMiddleware',
    'international.middleware.InternationalSiteMiddleware',
    'vinaigrette.middleware.VinaigretteAdminLanguageMiddleware'
]
```

This makes the current `CountrySite` object available through the request object. E.g., in views:

```python
def index(request):
    country_site = request.country_site
```

## Models

All models in a project can be made international, i.e. associated to countries and/or languages, by inheriting the `InternationalModel` base class.

```python
# models.py
from international.models import InternationalModel

class Product(InternationalModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
```

This will add the `country_sites` and `object_language` field and extend the model managers.

To filter all models associated with CountrySite `nl` or with language "en":

```python
products = Product.objects.by_country("nl")

products = Product.objects.by_language("en")
```

## Language

When using in combination with Django's [i18n translation](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/), add the `InternationalSiteMiddleware` before the Django `LocaleMiddleware` in your project's settings.

If you want to force using the `CountrySite.default_language` language for a given CountrySite, set `FORCE_COUNTRY_LANGUAGE` to True. This will make sure that for e.g. the German country site, `i18n` will use the German language that has been associated to the CountrySite. 

```python
# settings.py

FORCE_COUNTRY_LANGUAGE = True
```

## Country detection endpoint

The `international.views.get_country_from_request` is included that will return a JSON response with the detected visitor location based on their IP address when the MaxMind GeoIP2 library is installed. To use it, include `international.urls` in your project `urls.py`. This will include the `localize/` endpoint that only allows GET requests, with example response:

```
{
    "country": "NL",    # country code or null
    "detected": true    # false when the country could not be detected from the visitor IP
}
```

## International Sitemap

Use the International extension to the Django Sites Sitemap to create dynamic sitemaps based on the current request domain rather than a single fixed site domain. First, use [the Django Sitemaps like usual](https://docs.djangoproject.com/en/3.2/ref/contrib/sitemaps/) but instead of using the out-of-the-box `django.contrib.sites.sitemaps.views` import the same views from `international.sitemaps.views`, this will change the domain of the urls shown in the sitemap to that of the current request CountrySite instead of the hardcoded Site domain (which can only be one per application).

```python
from international.sitemaps import views as international_sitemap_views

# Register sitemap views

urlpatterns += (
    path(
        r"sitemap.xml", international_sitemap_views.index, {"sitemaps": sitemap_sections}
    ),
    path(
        "sitemap-<section>.xml",
        international_sitemap_views.sitemap,
        {"sitemaps": sitemap_sections},
        name="international.sitemaps.views.sitemap",
    ),
)
```

In order to limit/adjust the items shown in a sitemap based on the current request domain/current CountrySite. Inherit the `InternationalSitemap` extension in your Sitemap class (this is available for models that use `InternationalModel`), this wel make the country_code of the current request available inside the class methods. For example, here the blog post items shown in the sitemap are filtered by country code:

```python
from international.sitemaps import InternationalSitemap

class BlogSitemap(InternationalSitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Post.objects.by_country(self.country_code)

    def lastmod(self, obj):
        return obj.published_date
```

## Admin Mixins

### InternationalModelAdminMixin
_For models inheriting the InternationalModel class_

### TranslatedFieldsModelAdminMixin

_For models using Vinaigrette translated fields - not InternationalModel_

Extend model admin's with fields that use [django-vinaigrette](https://github.com/ecometrica/django-vinaigrette/) to add translations (using `gettext` instead of adding more fields in the db). In order to use this mixin the translated fields must be registerred to Vinaigrette in the app's config like below. Specifically, the `translated_fields` dictionary must be available in the AppConfig.

```python
class TestappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testapp'

    translated_fields = {
        'Certificate': ['description']
    } 

    def ready(self):

        for modelname in self.translated_fields.keys():
            model = self.get_model(modelname)

            # Register fields to translate
            vinaigrette.register(model, self.translated_fields[modelname])
```

This will show the _translated field_ indicator with all fields that can be translated in the translation files. It will also add the current translations to the bottom of the admin page (note: these are for reference and cannot be edited through the admin since they do not come from the database but the translation files)

![image](https://user-images.githubusercontent.com/9480738/132023303-570613d9-d7c8-42c0-a0b7-4cb6d9ddc5c6.png)

