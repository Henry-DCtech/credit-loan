from django import forms
from .models import LoanApplication

class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        fields = ['branch','full_name','age','photo','monthly_income','loan_amount','loan_tenure','credit_score','employment_years','existing_loans','marital_status']
        widgets = {
            'branch': forms.Select(attrs={'class':'form-select'}),
            'full_name': forms.TextInput(attrs={'class':'form-control'}),
            'age': forms.NumberInput(attrs={'class':'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class':'form-control'}),
            'loan_amount': forms.NumberInput(attrs={'class':'form-control'}),
            'loan_tenure': forms.NumberInput(attrs={'class':'form-control'}),
            'credit_score': forms.NumberInput(attrs={'class':'form-control'}),
            'employment_years': forms.NumberInput(attrs={'class':'form-control'}),
            'existing_loans': forms.NumberInput(attrs={'class':'form-control'}),
            'marital_status': forms.Select(attrs={'class':'form-select'}),
            'photo': forms.FileInput(attrs={'class':'form-control'}),
        }
    
from django.contrib.auth.models import User
from .models import Profile, BRANCHES
class OfficerRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[
        ('CEO', 'CEO'),
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('CREDIT_OFFICER', 'Credit Officer'),
        ('MIS', 'MIS Officer'),
    ])
    branch = forms.ChoiceField(choices=[
        ('LAGOS', 'LAGOS'),
        ('ABUJA', 'ABUJA'),
        ('KANO', 'KANO'),
        ('PORT_HARCOURT', 'PORT_HARCOURT'),
        ('ENUGU', 'ENUGU'),
        ('IBADAN', 'IBADAN'),
        ('ONDO', 'ONDO'),
        ('OSUN', 'OSUN'),
    ])

    def save(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        role = self.cleaned_data['role']
        branch = self.cleaned_data['branch']
        
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user, role=role, branch=branch)
        return user

from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name','phone_number','email','bvn','branch','address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class':'form-control'}),
            'phone_number': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'bvn': forms.TextInput(attrs={'class':'form-control'}),
            'branch': forms.Select(attrs={'class':'form-select'}),
            'address': forms.Textarea(attrs={'class':'form-control','rows':2}),
        }