from django.contrib.sitemaps import Sitemap
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class InternationalSitemap(Sitemap):
    """
    Extend django.contrib.sitemaps.Sitemap to add a self.country_code
    variable that is available in the get_items() function such that
    the Sitemap can be adjusted to only show items for the current 
    CountrySite.
    """
    
    # Initialize country_code with default value
    country_code = getattr(settings, "DEFAULT_COUNTRY_CODE")

    if not country_code:
        raise ImproperlyConfigured(
                "You're using the \"InternationalSitemap\" app without having set a DEFAULT_COUNTRY_CODE")

    def get_urls(self, page=1, site=None, protocol=None):
        protocol = self.get_protocol(protocol)
        domain = self.get_domain(site)
        return self._urls(page, protocol, domain, site)

    def _urls(self, page, protocol, domain, site):
        urls = []
        latest_lastmod = None
        all_items_lastmod = True  # track if all items have a lastmod

        # Set country_code based on the current request
        self.country_code = site.country_code

        paginator_page = self.paginator.page(page)
        for item in paginator_page.object_list:
            loc = f'{protocol}://{domain}{self._location(item)}'
            priority = self._get('priority', item)
            lastmod = self._get('lastmod', item)

            if all_items_lastmod:
                all_items_lastmod = lastmod is not None
                if (all_items_lastmod and
                        (latest_lastmod is None or lastmod > latest_lastmod)):
                    latest_lastmod = lastmod

            url_info = {
                'item': item,
                'location': loc,
                'lastmod': lastmod,
                'changefreq': self._get('changefreq', item),
                'priority': str(priority if priority is not None else ''),
                'alternates': [],
            }

            if self.i18n and self.alternates:
                for lang_code in self._languages():
                    loc = f'{protocol}://{domain}{self._location(item, lang_code)}'
                    url_info['alternates'].append({
                        'location': loc,
                        'lang_code': lang_code,
                    })
                if self.x_default:
                    lang_code = settings.LANGUAGE_CODE
                    loc = f'{protocol}://{domain}{self._location(item, lang_code)}'
                    loc = loc.replace(f'/{lang_code}/', '/', 1)
                    url_info['alternates'].append({
                        'location': loc,
                        'lang_code': 'x-default',
                    })

            urls.append(url_info)

        if all_items_lastmod and latest_lastmod:
            self.latest_lastmod = latest_lastmod

        return urls