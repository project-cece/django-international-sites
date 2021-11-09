from django.shortcuts import render
from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings 

def visitor_ip_address(request):
    """
    Parse visitor public IP adress from HTTP headers
    """

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_country_from_ip(request):
    """
    Check GeoIP2 library for visitor country based on IP
    """

    if not getattr(settings, "GEOIP_PATH", False):
        return None

    IP = visitor_ip_address(request)

    # Example
    # IP = "143.177.174.48"
    
    g = GeoIP2()

    try:
        country = g.country(IP)
    except:
        return None
    
    return country.get("country_code")