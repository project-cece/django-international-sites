from django.shortcuts import render
from django.contrib.gis.geoip2 import GeoIP2

def visitor_ip_address(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_country_from_ip(request):

	IP = visitor_ip_address(request)

	# Example
	# IP = "143.177.174.48"
	
	g = GeoIP2()

	try:
		country = g.country(IP)
	except:
		return None
    
	if country.get("country_code"):
		return country["country_code"]
