from django import forms

from agrinova.constants import TAMIL_NADU_DISTRICTS

from .models import BuyerPreference


class BuyerPreferenceForm(forms.ModelForm):
    class Meta:
        model = BuyerPreference
        fields = ('crop', 'quantity_needed', 'preferred_district')
        widgets = {
            'crop': forms.Select(attrs={'class': 'form-select'}),
            'quantity_needed': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_district'] = forms.ChoiceField(
            choices=[('', 'Any district')] + list(TAMIL_NADU_DISTRICTS),
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
