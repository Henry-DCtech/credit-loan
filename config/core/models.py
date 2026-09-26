from django.db import models
from django.contrib.auth.models import User

BRANCHES = [
    ('LAGOS','Lagos - HQ'),
    ('ABUJA','Abuja'),
    ('PH','Port Harcourt'),
    ('KANO','Kano'),
    ('IBADAN','Ibadan'),
    ('ENUGU','Enugu'),
]

class Profile(models.Model):
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('CREDIT_OFFICER', 'Credit Officer'),
        ('MIS', 'MIS Officer'),
            ]
   
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    branch = models.CharField(max_length=50, default='LAGOS')
    role = models.CharField(max_length=20, default='OFFICER', choices=[('CEO','CEO'),('OFFICER','OFFICER')])
    
    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.branch}"

BRANCHES = [('LAGOS','LAGOS'),('ABUJA','ABUJA'),('ENUGU','ENUGU'),('KANO','KANO')]

class LoanApplication(models.Model):
    
    # ADD THIS NEW FIELD
    assigned_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_loans')
    full_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=50, default='LAGOS')
    loan_amount = models.FloatField()
    # ... rest ...
    # Link to client (optional but recommended)
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.CharField(max_length=20, choices=BRANCHES, default='LAGOS')
    full_name = models.CharField(max_length=100)
    age = models.IntegerField()
    photo = models.ImageField(upload_to='applicants/', null=True, blank=True)
    monthly_income = models.FloatField()
    loan_amount = models.FloatField()
    loan_tenure = models.IntegerField(default=12)
    credit_score = models.IntegerField()
    employment_years = models.IntegerField()
    existing_loans = models.IntegerField(default=0)
    marital_status = models.CharField(max_length=20, default='Single')
    is_disbursed = models.BooleanField(default=False)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    repayment_due_date = models.DateField(null=True, blank=True)
    
    # --- ADD THESE 4 NEW FIELDS ---
    purpose = models.CharField(max_length=200, blank=True, default='Business')
    risk_score = models.FloatField(default=0)
    status = models.CharField(max_length=20, default='PENDING', choices=[('PENDING','PENDING'),('APPROVED','APPROVED'),('REJECTED','REJECTED')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.branch} - {self.status}"

class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    bvn = models.CharField(max_length=11, blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    branch = models.CharField(max_length=50, default='LAGOS')
    photo = models.ImageField(upload_to='clients/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.branch}"

class Repayment(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='repayments')
    branch = models.CharField(max_length=20, choices=BRANCHES, default='LAGOS')
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)
    def __str__(self): return f"Repay {self.amount} - {self.branch}"

class LoanDefault(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='defaults')
    branch = models.CharField(max_length=20, choices=BRANCHES, default='LAGOS')
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)
    id_alert = models.BooleanField(default=True)  # New field to indicate if an alert has been sent
    reason = models.CharField(max_length=200, default="You did not Pay your Repayment today")  # New field to store the reason for default
    
    def __str__(self): return f"Default {self.amount} - {self.branch}"

class BranchSaving(models.Model):
    branch = models.CharField(max_length=20, choices=BRANCHES, default='LAGOS')
    client_name = models.CharField(max_length=100, blank=True)
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)
    def __str__(self): return f"Saving {self.amount} - {self.branch}"