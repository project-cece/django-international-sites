
import copy

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.apps import apps
from django import forms

from django.utils.safestring import mark_safe
from django.contrib.admin.utils import flatten_fieldsets
from django.forms.models import fields_for_model
from django.utils import translation
from django.utils.translation import gettext_lazy as _


from .models import CountrySite

SMALL_ICON_STYLE = "float: right; height: 18px;"
COUNTRY_IMG_ICON = "<img src='{0}' data-toggle='tooltip' data-placement='left' \
            data-html='true' alt='{1}' title='{1}' style='{2}' />"

@admin.register(CountrySite)
class CountrySitedmin(admin.ModelAdmin):
    list_display = (
        "name_with_icon", "active", "country_code", "default_language", "domain",
    )

    def get_form(self, request, obj=None, **kwargs):
        """Add to default forms"""

        form = super(CountrySitedmin, self).get_form(request, obj, **kwargs)
        form.base_fields["default_language"] = forms.ChoiceField(choices=[("", ""),] + list(settings.LANGUAGES))

        return form

    def name_with_icon(self, obj):
        """
        Display icon as image if iconpath given in settings
        """

        if not getattr(settings, "SITE_ICON_DIR", False):
            return obj.name

        flag = "<img src='{0}' style='max-width: 50px; max-height: 18px;' />".format(obj.get_icon())
        return mark_safe("{0} &nbsp;&nbsp;&nbsp;{1}".format(flag, obj.name))

    name_with_icon.short_description = "name"


class InternationalModelAdminMixin:

    # filter_horizontal = ("country_sites",)

    list_filter = ("country_sites",) 

    def get_form(self, request, obj=None, **kwargs):
        """Add to default forms"""

        form = super(InternationalModelAdminMixin, self).get_form(request, obj, **kwargs)

        form.base_fields["country_sites"].label_from_instance = lambda obj: mark_safe(
            "{0} {1}".format(
                obj.name, 
                COUNTRY_IMG_ICON.format(obj.get_icon(), obj.name, SMALL_ICON_STYLE),
            )
        )
        form.base_fields["object_language"] = forms.ChoiceField(choices=[("", ""),] + list(settings.LANGUAGES))
        form.base_fields["object_language"].required = False

        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(InternationalModelAdminMixin, self).get_fieldsets(request, obj)

        while 'country_sites' in fieldsets[0][1]['fields']: fieldsets[0][1]['fields'].remove('country_sites') 
        while 'object_language' in fieldsets[0][1]['fields']: fieldsets[0][1]['fields'].remove('object_language')

        added = False
        for fields in fieldsets:

            if fields[0]:
                if "International" in fields[0]:
                    added = True
                    break

        if not added:
            fieldsets += [("International", {"fields": (('country_sites', 'object_language'),)})] 

        return fieldsets

    def display_country_sites(self, obj):
        show = ""
        for tmp in obj.country_sites.all():
            # If no images set, use country code
            if not getattr(settings, "SITE_ICON_DIR", False):
                icon = obj.country_code + ","
            else:
                icon = COUNTRY_IMG_ICON.format(tmp.get_icon(), tmp.name, SMALL_ICON_STYLE + "padding:1px;") 
            show += icon
            show += "<style>.column-display_country_sites{max-width: 85px;}</style>"
        return mark_safe(show)
    display_country_sites.short_description = "Country Sites"

    def display_language(self, obj):

        return 

class TranslatedFieldsModelAdminMixin:
    """
    Mixin for models that use Vinaigrette translated fields to show admins which fields
    are translated and the translations
    """
    INTRO = "Here you will find the translations in the available languages for the fields of \
    this item that have been marked as a Translation Field. The translations can be adapted \
    through the Translation Files. <br><br>Note: If you change the original version of the field above, \
    then the translation files also need to be updated."

    translated_fields = []
    translation_fields = []


    def get_fields(self, request, obj=None):
        fields = super(TranslatedFieldsModelAdminMixin, self).get_fields(request, obj)
        for field in self.translation_fields:
            while field in fields:
                fields.remove(field)

        return fields

    def __init__(self, *args, **kwargs):
        super(TranslatedFieldsModelAdminMixin, self).__init__(*args, **kwargs)
        app = self.model._meta.app_label
        app_config = apps.get_app_config(app)
        self.translated_fields = app_config.translated_fields.get(self.model._meta.object_name, [])

    def get_form(self, request, obj=None, change=False, **kwargs):

        fields = fields_for_model(self.model)
        kwargs['fields'] = fields

        form = super(TranslatedFieldsModelAdminMixin, self).get_form(request, obj, change, **kwargs)

        self.translation_fields = []

        for field in self.translated_fields:
            form.base_fields[field].label = mark_safe(form.base_fields[field].label +": <br><i style='font-size: smaller; font-variant: petite-caps; font-weight: normal;'>translated field</i>")

            if obj:
                for (lang, name) in settings.LANGUAGES:
                    if lang != settings.LANGUAGE_CODE:
                        new_field = field + "_" + lang
                        if new_field not in form.base_fields.keys():
                            form.base_fields[new_field] = copy.deepcopy(fields[field]) 
                            form.base_fields[new_field].label = new_field
                            form.base_fields[new_field].disabled = True
                            form.base_fields[new_field].required = False

                            if getattr(obj, field, None) != None:
                                with translation.override(lang):
                                    form.base_fields[new_field].initial = _(getattr(obj, field))

                            self.translation_fields.append(new_field)


        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(TranslatedFieldsModelAdminMixin, self).get_fieldsets(request, obj)
        fieldsets += [("International Translated Fields", {"fields": self.translation_fields, "description": self.INTRO})] 
        return fieldsets


