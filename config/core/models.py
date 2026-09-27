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


class FieldCollection(models.Model):

    STATUS_CHOICES = [
        ('PAID', 'PAID'),
        ('DEFAULT', 'DEFAULT'),
        ('PARTIAL', 'PARTIAL'),
    ]
    payment_status = models.CharField(max_length=10, choices=[('PAID','PAID'),('DEFAULT','DEFAULT'),('PARTIAL','PARTIAL')])    
    
    @property
    def total_savings_now(self):
        return (self.last_total_savings or 0) + (self.weekly_savings or 0)
    
    loan_stage = models.CharField(max_length=100, default='FIRST', help_text="e.g. FIRST, SECOND, 4th, 5th, 10th")
    
    officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    client_name = models.CharField(max_length=200) # Full Name
    client_id_code = models.CharField(max_length=50, blank=True) # optional
    branch = models.CharField(max_length=50, default='LAGOS')
    date = models.DateField(auto_now_add=True)

    # Savings
    weekly_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_total_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Weekly Loan
    loan_stage = models.CharField(max_length=100, default='FIRST', help_text="e.g. FIRST, SECOND, 4th, 5th, 10th")
    weekly_repayment_due = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Loan Repayment per Week', default=0)
    total_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    repayment_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Monthly Loan
    monthly_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monthly Loan Field', default=0)
    monthly_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_loan_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date','-created_at']
    
    def __str__(self):
        return f"{self.client_name} - {self.date}"

# models.py
class Loan(models.Model):
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    branch = models.CharField(max_length=100)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    total_due = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    weekly_due = models.DecimalField(max_digits=12, decimal_places=2)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client} - {self.balance}"
