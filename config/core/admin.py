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


from django.contrib import admin
from .models import BankLicense
from datetime import date, timedelta

@admin.register(BankLicense)
class BankLicenseAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'license_key', 'license_type', 'is_active', 'valid_until', 'days_left', 'is_valid_status')
    list_filter = ('is_active', 'license_type')
    search_fields = ('bank_name', 'license_key')
    actions = ['renew_30_days', 'renew_1_year', 'renew_10_years', 'deactivate_license']

    def days_left(self, obj):
        delta = obj.valid_until - date.today()
        return f"{delta.days} days" if delta.days >=0 else f"EXPIRED {-delta.days} days ago"
    days_left.short_description = "Days Left"

    def is_valid_status(self, obj):
        return "✅ VALID" if obj.is_valid() else "❌ EXPIRED"
    is_valid_status.short_description = "Status"

    @admin.action(description="Renew +30 Days (₦100k)")
    def renew_30_days(self, request, queryset):
        for lic in queryset:
            lic.valid_until = max(lic.valid_until, date.today()) + timedelta(days=30)
            lic.is_active = True
            lic.save()
        self.message_user(request, f"{queryset.count()} bank(s) renewed +30 days")

    @admin.action(description="Renew +1 Year (₦250k Annual)")
    def renew_1_year(self, request, queryset):
        for lic in queryset:
            lic.valid_until = max(lic.valid_until, date.today()) + timedelta(days=365)
            lic.is_active = True
            lic.license_type = 'ANNUAL'
            lic.save()
        self.message_user(request, f"{queryset.count()} bank(s) renewed +1 Year")

    @admin.action(description="Renew 10 Years - Outright (₦2.5M)")
    def renew_10_years(self, request, queryset):
        for lic in queryset:
            lic.valid_until = date.today() + timedelta(days=3650)
            lic.is_active = True
            lic.license_type = 'OUTRIGHT'
            lic.save()
        self.message_user(request, f"{queryset.count()} bank(s) set to OUTRIGHT (10 years)")

    @admin.action(description="Deactivate - Lock Bank")
    def deactivate_license(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} bank(s) DEACTIVATED - Software will lock")