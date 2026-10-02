from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BuyerPreferenceForm
from .models import BuyerPreference
from .scoring import get_recommended_buyers_for_seller, get_recommended_sellers_for_buyer


@login_required
def matching_page(request):
    user = request.user
    preference = BuyerPreference.objects.filter(buyer=user).first()
    form = BuyerPreferenceForm(instance=preference)

    if request.method == 'POST':
        form = BuyerPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            pref = form.save(commit=False)
            pref.buyer = user
            pref.save()
            return redirect('matching:matching')

    seller_recs = get_recommended_sellers_for_buyer(
        user,
        crop_id=preference.crop_id if preference else None,
        quantity_needed=preference.quantity_needed if preference else None,
        preferred_district=preference.preferred_district if preference else None,
    )
    buyer_recs = get_recommended_buyers_for_seller(user)

    return render(request, 'matching/matching.html', {
        'form': form,
        'seller_recommendations': seller_recs,
        'buyer_recommendations': buyer_recs,
    })
