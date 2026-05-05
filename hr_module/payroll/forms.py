from django import forms
from .models import Earning, Deduction

class EarningForm(forms.ModelForm):
    class Meta:
        model = Earning
        fields = ['employee', 'type', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class DeductionForm(forms.ModelForm):
    class Meta:
        model = Deduction
        fields = ['employee', 'type', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
