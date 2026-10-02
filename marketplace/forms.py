from django import forms

from agrinova.constants import TAMIL_NADU_DISTRICTS, UNIT_CHOICES

from .models import CropCategory, Listing


class ListingForm(forms.ModelForm):
    crop = forms.ModelChoiceField(
        queryset=CropCategory.objects.all(),
        empty_label='Select crop type',
    )

    class Meta:
        model = Listing
        fields = ('crop', 'quantity', 'unit', 'price_per_unit', 'description', 'district', 'image', 'image_url')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'Optional stock image URL', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'crop': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'] = forms.ChoiceField(
            choices=[('', 'Select district')] + list(TAMIL_NADU_DISTRICTS),
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        self.fields['unit'] = forms.ChoiceField(choices=UNIT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))


class ListingFilterForm(forms.Form):
    crop = forms.ModelChoiceField(
        queryset=CropCategory.objects.all(),
        required=False,
        empty_label='All crops',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    district = forms.ChoiceField(
        choices=[('', 'All districts')] + list(TAMIL_NADU_DISTRICTS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    q = forms.CharField(required=False, label='Search', widget=forms.TextInput(attrs={
        'placeholder': 'Search by crop name...',
        'class': 'form-control',
    }))
