from django import forms
from .models import Earning, Deduction

class EarningForm(forms.ModelForm):
    class Meta:
        model = Earning
        fields = ['employee', 'type', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'date': 'The earning will be included in the payslip for this month/year.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            self.fields['employee'].queryset = self.fields['employee'].queryset.filter(branch=user.branch)

class DeductionForm(forms.ModelForm):
    class Meta:
        model = Deduction
        fields = ['employee', 'type', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'date': 'The deduction will be included in the payslip for this month/year.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            self.fields['employee'].queryset = self.fields['employee'].queryset.filter(branch=user.branch)
