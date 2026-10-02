from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ListingFilterForm, ListingForm
from .models import Listing


class ListingListView(ListView):
    model = Listing
    template_name = 'marketplace/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        qs = Listing.objects.filter(is_active=True).select_related('crop', 'seller')
        self.filter_form = ListingFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            crop = self.filter_form.cleaned_data.get('crop')
            district = self.filter_form.cleaned_data.get('district')
            q = self.filter_form.cleaned_data.get('q')
            if crop:
                qs = qs.filter(crop=crop)
            if district:
                qs = qs.filter(district=district)
            if q:
                qs = qs.filter(Q(crop__name__icontains=q) | Q(description__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context


class ListingDetailView(DetailView):
    model = Listing
    template_name = 'marketplace/listing_detail.html'
    context_object_name = 'listing'

    def get_queryset(self):
        return Listing.objects.filter(is_active=True).select_related('crop', 'seller')


class ListingCreateView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = 'marketplace/listing_form.html'
    success_url = reverse_lazy('marketplace:listing_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        self.request.user.is_listing_as_seller = True
        self.request.user.save(update_fields=['is_listing_as_seller'])
        return super().form_valid(form)


class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = 'marketplace/listing_form.html'
    success_url = reverse_lazy('marketplace:listing_list')

    def test_func(self):
        listing = self.get_object()
        return self.request.user == listing.seller or self.request.user.is_staff


class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Listing
    template_name = 'marketplace/listing_confirm_delete.html'
    success_url = reverse_lazy('marketplace:listing_list')

    def test_func(self):
        listing = self.get_object()
        return self.request.user == listing.seller or self.request.user.is_staff
