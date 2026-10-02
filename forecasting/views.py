from django.shortcuts import render
from django.utils.safestring import mark_safe
import json

from agrinova.constants import TAMIL_NADU_DISTRICTS
from marketplace.models import CropCategory

from .forecast_engine import forecast_prices


def forecast_page(request):
    crops = CropCategory.objects.all()
    districts = TAMIL_NADU_DISTRICTS
    result = None
    selected_crop = request.GET.get('crop')
    selected_district = request.GET.get('district')

    if selected_crop and selected_district:
        try:
            crop = CropCategory.objects.get(id=selected_crop)
            result = forecast_prices(crop, selected_district)
            if result and not result.get('error'):
                result['historical_json'] = mark_safe(json.dumps(result['historical']))
                result['forecast_json'] = mark_safe(json.dumps(result['forecast']))
        except CropCategory.DoesNotExist:
            result = {'error': 'Crop not found.'}

    return render(request, 'forecasting/forecast.html', {
        'crops': crops,
        'districts': districts,
        'result': result,
        'selected_crop': selected_crop,
        'selected_district': selected_district,
    })
