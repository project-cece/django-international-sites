# Django International 

A single application to server multiple domains and country sites. 

## Install

- `pip install django-international-sites-0.1.0.tar.gz`
- Add "international" to `INSTALLED_APPS` in `settings.py`
- Run `python manage.py migrate international`
- Add `CountrySite` objects in admin `/admin/international/countrysite/`

## Settings

```python
# Fallback country code
DEFAULT_COUNTRY_CODE = "NL"

# Map domains uniquely to a single country code (optional)
UNIQUE_DOMAINS = {"projectcece.nl": "nl", "projectcece.co.uk": "uk"}

# Directory for site icons to be displayed in admin (optional)
SITE_ICON_DIR = "static/site_icons/"
```

## Request middleware

How is the country code detected from the request?

1. If unique domain name (e.g. projectcece.nl), use country data of related country code
2. If country code is forced as url parameter (i.e. projectcece.com/c=fr), use that country code
3. If a cookie with location preference is used, use that country code
4. Check location based on visitor IP address, use that country code
5. If nothing could be detected, use default country code

Add the middleware to settings:

```python
MIDDLEWARE = [
	...
    'international.middleware.InternationalSiteMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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

