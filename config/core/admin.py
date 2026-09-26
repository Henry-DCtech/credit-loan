from django.contrib import admin
from django.contrib.auth.models import User
from.models import Profile, Client, LoanApplication

# --- 1. User with Profile Inline ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0

class UserAdmin(admin.ModelAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'get_role', 'get_branch', 'is_staff']

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'

    def get_branch(self, obj):
        return obj.profile.branch if hasattr(obj, 'profile') else '-'
    get_branch.short_description = 'Branch'

# Re-register User
try:
    admin.site.unregister(User)
except:
    pass
admin.site.register(User, UserAdmin)

# --- 2. Profile Admin (only ONE) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'branch', 'id']
    list_filter = ['role', 'branch']
    search_fields = ['user__username']
    list_editable = ['role', 'branch']

# --- 3. Loan Admin ---
@admin.register(LoanApplication)
class LoanAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'branch', 'loan_amount', 'monthly_income', 'credit_score', 'risk_score', 'status', 'created_at')
    list_filter = ('status', 'branch', 'created_at')
    list_editable = ('status',)
    search_fields = ('full_name', 'branch')
    ordering = ('-created_at',)

# --- 4. Client Admin ---
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'branch', 'phone_number', 'national_id', 'created_at')
    list_filter = ('branch', 'created_at')
    search_fields = ('full_name', 'phone_number', 'national_id')

from .models import Repayment, LoanDefault, BranchSaving

@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('id','loan','branch','amount','date')
    list_filter = ('branch','date')

@admin.register(LoanDefault)
class DefaultAdmin(admin.ModelAdmin):
    list_display = ('id','loan','branch','amount','date')
    list_filter = ('branch','date')

@admin.register(BranchSaving)
class SavingAdmin(admin.ModelAdmin):
    list_display = ('id','branch','client_name','amount','date')
    list_filter = ('branch','date')