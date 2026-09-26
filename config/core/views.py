from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import date, timedelta

from .models import LoanApplication, Profile, Client, Repayment, LoanDefault, BranchSaving
from .forms import LoanApplicationForm, OfficerRegistrationForm

def landing(request):
    return render(request, 'core/landing.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('landing')

@login_required
def register_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    if profile.role not in ['CEO', 'ADMIN']:
        messages.error(request, "Access Denied: Only CEO/Admin can register officers.")
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'OFFICER')
        branch = request.POST.get('branch', 'LAGOS')

        if role == 'CEO' and profile.role != 'CEO':
            messages.error(request, "Only CEO can create another CEO.")
            return redirect('register')
        if role == 'CEO' and profile.role == 'ADMIN':
            messages.error(request, "ADMIN cannot create CEO.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
        else:
            u = User.objects.create_user(username, '', password)
            Profile.objects.create(user=u, role=role, branch=branch)
            messages.success(request, f"{role} account '{username}' created in {branch}")
            return redirect('register')

    all_profiles = Profile.objects.select_related('user').all()
    return render(request, 'core/register.html', {'profile': profile, 'all_profiles': all_profiles})

@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    
    is_ceo = request.user.is_superuser or profile.role == 'CEO' or request.user.username == 'CEO'

    if is_ceo:
        loans = LoanApplication.objects.all()
        clients = Client.objects.all()
        repay_today_qs = Repayment.objects.filter(date=date.today())
        default_today_qs = LoanDefault.objects.filter(date=date.today())
        saving_today_qs = BranchSaving.objects.filter(date=date.today())
        base_qs = LoanApplication.objects.all()
    else:
        loans = LoanApplication.objects.filter(branch=profile.branch)
        clients = Client.objects.filter(branch=profile.branch)
        repay_today_qs = Repayment.objects.filter(branch=profile.branch, date=date.today())
        default_today_qs = LoanDefault.objects.filter(branch=profile.branch, date=date.today())
        saving_today_qs = BranchSaving.objects.filter(branch=profile.branch, date=date.today())
        base_qs = LoanApplication.objects.filter(branch=profile.branch)

    total = loans.count()
    pending = loans.filter(status='PENDING').count()
    approved = loans.filter(status='APPROVED').count()
    rejected = loans.filter(status='REJECTED').count()
    total_clients = clients.count()
    
    total_repay_today = repay_today_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    total_default_today = default_today_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    total_saving_today = saving_today_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    
    status_data = [approved, pending, rejected]
    
    monthly = loans.annotate(month=TruncMonth('created_at')).values('month').annotate(c=Count('id')).order_by('month')[:6]
    months = [m['month'].strftime('%b') if m['month'] else 'N/A' for m in monthly if m['month']]
    counts = [m['c'] for m in monthly if m['month']]
    
    if not months:
        months = ['Jan','Feb','Mar','Apr','May','Jun']
        counts = [0,0,0,0,0,0]

    recent_loans = loans.order_by('-id')[:5]

    # Default alerts - filter BEFORE slice
    base_default_qs = base_qs.filter(
        repayment_due_date__lt=date.today(),
        is_disbursed=True, 
        status='APPROVED'
    )
    total_defaulters = base_default_qs.count()
    default_alerts = base_default_qs.order_by('-repayment_due_date')[:10]

    # Disbursed today
    base_disbursed_qs = base_qs.filter(is_disbursed=True, disbursed_at__date=date.today())
    disbursed_today = base_disbursed_qs.aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0
    disbursed_count_today = base_disbursed_qs.count()

    context = {
        'profile': profile,
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'total_clients': total_clients,
        'recent_loans': recent_loans,
        'repay_today': total_repay_today,
        'default_today': total_default_today,
        'saving_today': total_saving_today,
        'status_json': json.dumps(status_data),
        'months_json': json.dumps(months),
        'counts_json': json.dumps(counts),
        'disbursed_today': disbursed_today,
        'disbursed_count_today': disbursed_count_today,
        'default_alerts': default_alerts,
        'total_defaulters': total_defaulters,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def apply_loan(request):
    from django.db import models
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    client_id = request.GET.get('client') or request.POST.get('client_id')
    selected_client = Client.objects.filter(pk=client_id).first() if client_id else None

    if request.method == 'POST':
        try:
            data = {
                'full_name': request.POST.get('full_name') or (selected_client.full_name if selected_client else 'Unknown'),
                'branch': request.POST.get('branch', 'LAGOS'),
                'loan_amount': float(request.POST.get('amount') or 50000),
                'amount': float(request.POST.get('amount') or 50000),
                'age': int(request.POST.get('age') or 30),
                'monthly_income': float(request.POST.get('monthly_income') or 100000),
                'income': float(request.POST.get('monthly_income') or 100000),
                'purpose': request.POST.get('purpose', 'Business'),
                'credit_score': int(request.POST.get('credit_score') or 650),
                'risk_score': 15,
                'status': 'PENDING',
                'employment_years': int(request.POST.get('employment_years') or 2),
                'employment_length': int(request.POST.get('employment_years') or 2),
            }
            if selected_client:
                data['client'] = selected_client
                # auto fill from client if exists
                if hasattr(selected_client, 'age'): data['age'] = selected_client.age
                if hasattr(selected_client, 'monthly_income'): data['monthly_income'] = selected_client.monthly_income

            # Build only fields that exist in YOUR model
            valid_fields = {f.name for f in LoanApplication._meta.get_fields() if hasattr(f, 'name')}
            create_data = {k: v for k, v in data.items() if k in valid_fields}

            # Fill any other required field with dummy value so it NEVER fails
            for fname in valid_fields:
                if fname in create_data or fname in ['id', 'client', 'created_at', 'updated_at', 'date_created', 'photo']: continue
                try:
                    f = LoanApplication._meta.get_field(fname)
                    if not f.null and f.default == models.NOT_PROVIDED:
                        if isinstance(f, (models.IntegerField, models.FloatField, models.DecimalField)):
                            create_data[fname] = 0
                        elif isinstance(f, (models.CharField, models.TextField)):
                            create_data[fname] = 'N/A'
                except: pass

            print("FINAL CREATE DATA:", create_data)
            loan = LoanApplication.objects.create(**create_data)
            messages.success(request, f"Application #{loan.id} submitted for CEO Review")
            return redirect('applications')
        except Exception as e:
            import traceback; traceback.print_exc()
            messages.error(request, f"Error: {e}")

    return render(request, 'core/apply.html', {
        'profile': profile,
        'selected_client': selected_client,
        'clients': Client.objects.all()[:50]
    })

@login_required
def applications(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    role = profile.role
    
    qs = LoanApplication.objects.all().order_by('-created_at')
    
    # 1. BRANCH FILTER (except CEO)
    if role not in ['CEO'] and not request.user.is_superuser:
        qs = qs.filter(branch=profile.branch)
    
    # 2. APPROVED LOANS - CEO ONLY
    view_mode = request.GET.get('view', 'ALL')
    if view_mode == 'APPROVED':
        if role != 'CEO' and not request.user.is_superuser and request.user.username != 'CEO':
            messages.error(request, "Only CEO can view Approved Loans page")
            return redirect('dashboard')
        qs = qs.filter(status='APPROVED')

    # Normal filters
    status_filter = request.GET.get('status')
    branch_filter = request.GET.get('branch')
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)
    if branch_filter and branch_filter != 'ALL':
        qs = qs.filter(branch=branch_filter)
    
    # For Assign Officer dropdown
    officers = Profile.objects.filter(role__in=['OFFICER', 'CREDIT_OFFICER', 'BRANCH_MANAGER']).select_related('user')
    
    return render(request, 'core/applications.html', {
        'applications': qs, 
        'role': role, 
        'profile': profile,
        'officers': officers,
        'view_mode': view_mode
    })


def analyzer(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None

    result = None
    risk_score = None
    decision = None
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        if amount > 2000000:
            risk_score = 75.0
            decision = "REJECTED"
        else:
            risk_score = 15.0
            decision = "APPROVED"
        result = True

    return render(request, 'core/analyzer.html', {
        'profile': profile, 'result': result, 'risk_score': risk_score, 'decision': decision
    })

@login_required
def ceo_approve(request, pk):
    profile = request.user.profile
    if profile.role != 'CEO' and not request.user.is_superuser and request.user.username != 'CEO':
        messages.error(request, "Only CEO can approve")
        return redirect('applications')
    loan = get_object_or_404(LoanApplication, pk=pk)
    loan.status = 'APPROVED'
    loan.repayment_due_date = date.today() + timedelta(days=30)
    loan.save()
    messages.success(request, f"Loan #{loan.id} APPROVED")
    return redirect('applications')

@login_required
def reject_loan(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    loan.status = 'REJECTED'
    loan.save()
    messages.warning(request, f"Loan #{loan.id} rejected")
    return redirect('applications')

@login_required
def disburse_loan(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not loan.is_disbursed:
        loan.is_disbursed = True
        loan.disbursed_at = timezone.now()
        loan.status = 'APPROVED'
        loan.save()
        try:
            client_email = loan.client.email if loan.client and hasattr(loan.client, 'email') else None
            if client_email:
                send_mail(
                    f"Loan Disbursed - N{loan.loan_amount:,.0f}",
                    f"Hello {loan.full_name},\nYour loan N{loan.loan_amount:,.0f} has been disbursed.",
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@credit.com'),
                    [client_email],
                    fail_silently=True
                )
        except:
            pass
        messages.success(request, f"Disbursed N{loan.loan_amount} to {loan.full_name}")
    return redirect('applications')

@login_required
def staff_list_view(request):
    my_profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    if my_profile.role not in ['CEO','ADMIN']:
        messages.error(request, "Only CEO/ADMIN can view staff")
        return redirect('dashboard')
    all_profiles = Profile.objects.select_related('user').all().order_by('-id')
    return render(request, 'core/staff.html', {'profiles': all_profiles, 'profile': my_profile})

@login_required
def edit_staff_role(request, user_id):
    my_profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'role':'OFFICER','branch':'LAGOS'})
    if my_profile.role not in ['CEO','ADMIN']:
        messages.error(request, "Access denied")
        return redirect('dashboard')
    target_profile = get_object_or_404(Profile, id=user_id)
    if my_profile.role == 'ADMIN' and target_profile.role == 'CEO':
        messages.error(request, "ADMIN cannot edit CEO")
        return redirect('staff_list')
    if request.method == 'POST':
        new_role = request.POST.get('role')
        new_branch = request.POST.get('branch')
        if my_profile.role == 'ADMIN' and new_role == 'CEO':
            messages.error(request, "ADMIN cannot assign CEO")
            return redirect('staff_list')
        target_profile.role = new_role
        target_profile.branch = new_branch
        target_profile.save()
        messages.success(request, f"{target_profile.user.username} now {new_role}")
        return redirect('staff_list')
    return render(request, 'core/edit_role.html', {'target_profile': target_profile, 'profile': my_profile})

@login_required
def register_officer(request):
    profile = request.user.profile
    if profile.role != 'CEO' and not request.user.is_superuser:
        messages.error(request, "Only CEO can register officers")
        return redirect('dashboard')
    if request.method == 'POST':
        form = OfficerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Officer {form.cleaned_data['username']} created")
            return redirect('dashboard')
    else:
        form = OfficerRegistrationForm()
    return render(request, 'core/register_officer.html', {'form': form})

@login_required
def client_list(request):
    profile = request.user.profile
    clients = Client.objects.all().order_by('-id')
    if not (request.user.is_superuser or profile.role == 'CEO'):
        clients = clients.filter(branch=profile.branch)
    return render(request, 'core/client_list.html', {'clients': clients, 'profile': profile})

@login_required
def client_create(request):
    if request.method == 'POST':
        client = Client.objects.create(
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            bvn=request.POST.get('bvn'),
            address=request.POST.get('address'),
            branch=request.POST.get('branch'),
            created_by=request.user
        )
        if request.FILES.get('photo'):
            client.photo = request.FILES.get('photo')
            client.save()
        messages.success(request, f"Client {client.full_name} created")
        return redirect('client_list')
    return render(request, 'core/client_form.html')

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    loans = client.loans.all() if hasattr(client, 'loans') else client.loanapplication_set.all()
    return render(request, 'core/client_detail.html', {'client': client, 'loans': loans})

# Aliases
approve_loan = ceo_approve


@login_required
def assign_officer(request, pk):
    profile = request.user.profile
    if profile.role not in ['CEO', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, "Only CEO and ADMIN can assign officers")
        return redirect('applications')
    
    loan = get_object_or_404(LoanApplication, pk=pk)
    officer_id = request.POST.get('officer_id')
    if officer_id:
        user = get_object_or_404(User, id=officer_id)
        loan.assigned_officer = user
        loan.save()
        messages.success(request, f"{user.username} assigned to Loan #{loan.id}")
    return redirect('applications')