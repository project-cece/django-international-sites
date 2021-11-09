from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from international import localize

def get_country_data_from_request(request):
	country = localize.get_country_from_ip(request)

	data = {
		"country": country,
		"detected": True if country else False,
	}

	return data	

@require_http_methods(["GET"])
def get_country_from_request(request):
	return JsonResponse(get_country_data_from_request(request))