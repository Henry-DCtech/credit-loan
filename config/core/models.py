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

ROLE_CHOICES = [
    ('CEO', 'CEO'),
    ('ADMIN', 'Admin'),
    ('MANAGER', 'Manager'),
    ('OFFICER', 'Officer'),
    ('CREDIT_OFFICER', 'Credit Officer'),
    ('MIS', 'MIS Officer'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    branch = models.CharField(max_length=50, choices=BRANCHES, default='LAGOS')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OFFICER')
    
    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.branch}"

class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    bvn = models.CharField(max_length=11, blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    branch = models.CharField(max_length=50, choices=BRANCHES, default='LAGOS')
    photo = models.ImageField(upload_to='clients/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.branch}"

class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING','PENDING'),
        ('APPROVED','APPROVED'),
        ('REJECTED','REJECTED'),
        ('REVIEW', 'REVIEW'),
        ('DISBURSED', 'DISBURSED'),
    ]

    # Relationships
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_loans')

    # Core fields
    full_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=50, choices=BRANCHES, default='LAGOS')
    age = models.IntegerField(default=30)
    photo = models.ImageField(upload_to='applicants/', null=True, blank=True)
    
    monthly_income = models.FloatField(default=100000)
    loan_amount = models.FloatField(default=50000)
    loan_tenure = models.IntegerField(default=12)
    
    credit_score = models.IntegerField(default=650)
    employment_years = models.IntegerField(default=2)
    existing_loans = models.IntegerField(default=0)
    marital_status = models.CharField(max_length=20, default='Single')
    
    purpose = models.CharField(max_length=200, blank=True, default='Business')
    risk_score = models.FloatField(default=0)
    status = models.CharField(max_length=20, default='PENDING', choices=STATUS_CHOICES)
    
    is_disbursed = models.BooleanField(default=False)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    repayment_due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # FIX: alias so {{ loan.amount }} never crashes again
    @property
    def amount(self):
        return self.loan_amount

    @property
    def loan_type(self):
        return self.purpose

    def __str__(self):
        return f"{self.full_name} - {self.branch} - {self.status}"

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
    id_alert = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, default="You did not Pay your Repayment today")
    def __str__(self): return f"Default {self.amount} - {self.branch}"

class BranchSaving(models.Model):
    branch = models.CharField(max_length=20, choices=BRANCHES, default='LAGOS')
    client_name = models.CharField(max_length=100, blank=True)
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)
    def __str__(self): return f"Saving {self.amount} - {self.branch}"