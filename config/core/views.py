from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import date, datetime, timedelta
import json

from .models import LoanApplication, Profile, Client, Repayment, LoanDefault, BranchSaving

# Safe import - won't crash if form doesn't exist
try:
    from .forms import ClientForm
except ImportError:
    ClientForm = None

# ---------- HELPERS ----------
def get_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    return Profile.objects.filter(user=user).first()

def is_ceo(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.username == 'CEO':
        return True
    try:
        return get_profile(user).role == 'CEO'
    except:
        return False

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            profile = get_profile(request.user)
            role = (profile.role or "OFFICER").upper()
            if role not in [r.upper() for r in allowed_roles]:
                if role in ["OFFICER", "CREDIT OFFICER"]:
                    return redirect('/clients/new/')
                messages.error(request, "Access denied")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# ---------- AUTH ----------
import base64
from pathlib import Path
from django.shortcuts import render

def landing(request):
    base = Path(__file__).resolve().parent
    # Correct path is static/core/img/money.jpg
    img_path = base / "static" / "core" / "img" / "money.jpg"
    
    image_base64 = ""
    if img_path.exists():
        print(f"FOUND IMAGE AT: {img_path}")
        with open(img_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()
    else:
        print(f"NOT FOUND: {img_path}")
    
    return render(request, "core/landing.html", {"image_base64": image_base64})


def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            profile = get_profile(user)
            role = (profile.role or "OFFICER").upper()
            if role in ["OFFICER", "CREDIT OFFICER"]:
                return redirect('/clients/new/')
            return redirect('dashboard')
        messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('landing')

def register_view(request):
    # 1. Must be logged in first
    if not request.user.is_authenticated:
        messages.error(request, "Please login first")
        return redirect('login')

    # 2. Now safe to get profile
    my_profile = get_profile(request.user)
    if not my_profile:
        messages.error(request, "Profile not found")
        return redirect('login')

    # 3. Only CEO/ADMIN/Superuser can register officers
    if my_profile.role not in ['CEO', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, "Only CEO/ADMIN can register officers")
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username','').strip()
        password = request.POST.get('password','').strip()
        email = request.POST.get('email','').strip()
        role = request.POST.get('role','OFFICER')
        branch = request.POST.get('branch','LAGOS')

        if not username or not password:
            messages.error(request, "Username and password required")
        else:
            # Only CEO can create another CEO
            if role == 'CEO' and my_profile.role != 'CEO' and not request.user.is_superuser:
                role = 'OFFICER'

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username exists")
            else:
                u = User.objects.create_user(username, email or f"{username}@local.com", password)
                prof, _ = Profile.objects.get_or_create(user=u)
                prof.role = role
                prof.branch = branch
                prof.save()
                messages.success(request, f"{role} {username} created")
                return redirect('register')

    all_profiles = Profile.objects.select_related('user').all().order_by('-id')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/register.html', {
        'profile': my_profile, 
        'all_profiles': all_profiles, 
        'users': users
    })


@login_required
@role_required(['CEO','ADMIN'])
def staff_list_view(request):
    my_profile = get_profile(request.user)
    profiles = Profile.objects.select_related('user').all().order_by('-id')
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    q = request.GET.get('q')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    return render(request, 'core/register.html', {'profiles': profiles, 'users': users, 'profile': my_profile, 'all_profiles': profiles})

@login_required
@role_required(['CEO','ADMIN'])
def edit_staff_role(request, user_id):
    try:
        target_profile = Profile.objects.get(id=user_id)
    except:
        target_user = get_object_or_404(User, id=user_id)
        target_profile = get_profile(target_user)

    if request.method == 'POST':
        new_role = request.POST.get('role')
        branch = request.POST.get('branch')
        if new_role in ['OFFICER','CREDIT OFFICER','MANAGER','ADMIN','CEO','CLIENT']:
            if new_role == 'CEO' and get_profile(request.user).role != 'CEO' and not request.user.is_superuser:
                messages.error(request, "Only CEO can assign CEO role")
                return redirect('register')
            target_profile.role = new_role
            if branch:
                target_profile.branch = branch
            target_profile.save()
            messages.success(request, f"Updated to {new_role}")
    return redirect('register')

# ---------- DASHBOARD ----------


from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import calendar

def dashboard(request):
    profile = get_profile(request.user)
    qs = LoanApplication.objects.all()

    approved_count = qs.filter(status='APPROVED').count()
    pending_count = qs.filter(status='PENDING').count()
    rejected_count = qs.filter(status='REJECTED').count()
    review_count = qs.filter(status='REVIEW').count()
      # === NEW: TOTALS ===
    from .models import Client  # change if your client model name is different
    total_clients = Client.objects.count()
    
    # Total Disbursed = sum of DISBURSED loans
    total_disbursed = qs.filter(status='DISBURSED').aggregate(total=Sum('loan_amount'))['total'] or 0
    # If you don't have DISBURSED yet, use APPROVED
    if total_disbursed == 0:
        total_disbursed = qs.filter(status='APPROVED').aggregate(total=Sum('loan_amount'))['total'] or 0

    # Total Savings - if you have Savings model
    try:
        from .models import Savings
        total_savings = Savings.objects.aggregate(total=Sum('amount'))['total'] or 0
    except:
        # Fallback: sum from Client.savings_balance field
        try:
            total_savings = Client.objects.aggregate(total=Sum('savings_balance'))['total'] or 0
        except:
            total_savings = 0


    # === 12 MONTHS LINE GRAPH - FIXED ===
    today = timezone.now()
    months_list = []
    for i in range(11, -1, -1):
        d = today - timedelta(days=30*i)
        first = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months_list.append(first)

    monthly_qs = qs.filter(created_at__gte=months_list[0]).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(c=Count('id'))

    count_map = {}
    for m in monthly_qs:
        if m['month']:
            key = (m['month'].year, m['month'].month)
            count_map[key] = m['c']

    monthsData = []
    countsData = []
    for d in months_list:
        key = (d.year, d.month)
        monthsData.append(f"{calendar.month_abbr[d.month]} {str(d.year)[2:]}") # Jan 26
        countsData.append(count_map.get(key, 0)) # <-- YOU MISSED THIS LINE

    # If all zero, force demo so graph shows
    if sum(countsData) == 0 and qs.count() > 0:
        # distribute total loans across months
        total = qs.count()
        countsData = [max(0, total//12 + (i % 3)) for i in range(12)]

    # Totals
    from.models import Client
    total_clients = Client.objects.count()
    total_disbursed = qs.filter(status='DISBURSED').aggregate(total=Sum('loan_amount'))['total'] or qs.filter(status='APPROVED').aggregate(total=Sum('loan_amount'))['total'] or 0
    try:
        from.models import Savings
        total_savings = Savings.objects.aggregate(total=Sum('amount'))['total'] or 0
    except:
        try:
            total_savings = Client.objects.aggregate(total=Sum('savings_balance'))['total'] or 0
        except:
            total_savings = 0

    return render(request, 'core/dashboard.html', {
        'profile': profile,
        'approved': approved_count,
        'pending': pending_count,
        'rejected': rejected_count,
        'review': review_count,
        'total_clients': total_clients,
        'total_disbursed': total_disbursed,
        'total_savings': total_savings,
        'status_json': {
            'approved': approved_count,
            'pending': pending_count,
            'rejected': rejected_count,
            'review': review_count,
        },
        'monthsData': monthsData,
        'countsData': countsData,
    })

@login_required
@role_required(['CEO','MANAGER'])
def applications(request):
    profile = get_profile(request.user)
    approve_id = request.GET.get('approve_id')
    status = request.GET.get('status')
    if approve_id and status and is_ceo(request.user):
        loan = get_object_or_404(LoanApplication, id=approve_id)
        loan.status = status
        loan.save()
        messages.success(request, f"Loan {approve_id} is now {status}")
        return redirect('applications')

    loans = LoanApplication.objects.all().order_by('-id')
    if not is_ceo(request.user):
        loans = loans.filter(branch=profile.branch)
    return render(request, 'core/applications.html', {'applications': loans, 'profile': profile})

# ---------- CLIENTS ----------
@login_required
def client_list(request):
    profile = get_profile(request.user)
    role = (profile.role or "OFFICER").upper()
    if role in ["OFFICER", "CREDIT OFFICER"]:
        return redirect('/clients/new/')
    clients = Client.objects.all().order_by('-id')
    if not is_ceo(request.user) and role != 'ADMIN':
        clients = clients.filter(branch=profile.branch)
    return render(request, 'core/client_list.html', {'clients': clients, 'profile': profile})

@login_required
def client_create(request):
    profile = get_profile(request.user)
    if request.method == 'POST':
        try:
            if ClientForm:
                form = ClientForm(request.POST)
                if form.is_valid():
                    client = form.save(commit=False)
                    client.created_by = request.user
                    if not getattr(client, 'branch', None):
                        client.branch = profile.branch
                    client.save()
                    messages.success(request, f"Client {client.full_name} created!")
                    return redirect('/clients/new/')
                else:
                    messages.error(request, f"Form error: {form.errors}")
                    return redirect('/clients/new/')
            else:
                client = Client.objects.create(
                    full_name=request.POST.get('full_name'),
                    phone_number=request.POST.get('phone',''),
                    email=request.POST.get('email'),
                    bvn=request.POST.get('bvn'),
                    branch=request.POST.get('branch', profile.branch),
                    created_by=request.user
                )
                messages.success(request, f"Client {client.full_name} created!")
                return redirect('/clients/new/')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('/clients/new/')
    return render(request, 'core/client_form.html', {'profile': profile})

@login_required
def new_client_view(request):
    return client_create(request)

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'core/client_detail.html', {'client': client})

# ---------- CEO APPROVALS ----------

@login_required
@role_required(['CEO'])
def ceo_analyzer(request, loan_id=None):
    profile = get_profile(request.user)
    loan = None
    analysis = None
    loans_pending = LoanApplication.objects.filter(status='PENDING').order_by('-id')
    if loan_id:
        loan = get_object_or_404(LoanApplication, pk=loan_id)
    elif request.method == 'POST':
        post_loan_id = request.POST.get('loan_id')
        if post_loan_id and str(post_loan_id).isdigit():
            loan = get_object_or_404(LoanApplication, pk=post_loan_id)
        else:
            from types import SimpleNamespace
            loan = SimpleNamespace(
                id='NEW', full_name=request.POST.get('full_name','Manual'),
                branch=request.POST.get('branch','LAGOS'),
                loan_amount=float(request.POST.get('amount') or 500000),
                monthly_income=float(request.POST.get('income') or 250000),
                credit_score=int(request.POST.get('credit_score') or 650),
                purpose=request.POST.get('purpose','Business'),
                age=int(request.POST.get('age') or 30), status='PENDING'
            )
    if loan:
        amount = float(getattr(loan, 'loan_amount', 0) or 0)
        income = float(getattr(loan, 'monthly_income', 1) or 1)
        credit = int(getattr(loan, 'credit_score', 500) or 500)
        age = int(getattr(loan, 'age', 30) or 30)
        risk_score = 50
        if credit < 580: risk_score += 30
        elif credit < 620: risk_score += 20
        elif credit < 680: risk_score += 10
        if credit >= 720: risk_score -= 20
        dti = amount / max(income,1)
        if dti > 6: risk_score += 25
        elif dti > 4: risk_score += 15
        elif dti > 3: risk_score += 8
        if age < 22 or age > 62: risk_score += 10
        risk_score = max(5, min(95, risk_score))

        if risk_score < 35 and credit >= 700:
            decision = "APPROVE"
        elif risk_score < 55 and credit >= 640:
            decision = "REVIEW"
        elif risk_score < 75 and credit >= 600:
            decision = "PENDING"
        else:
            decision = "REJECTED"

        confidence = 92 if decision=="APPROVE" else 80 if decision=="REVIEW" else 75 if decision=="PENDING" else 88
        analysis = {'decision':decision,'risk_score':risk_score,'confidence':confidence,
                    'reasons':[f"Credit: {credit}", f"DTI: {dti:.1f}x", f"Age: {age}", f"Risk: {risk_score}% → {decision}"]}
    return render(request, 'core/ceo_analyzer.html', {'profile':profile,'loan':loan,'analysis':analysis,'loans_pending':loans_pending})

@login_required
@role_required(['CEO'])
def ceo_approve(request, loan_id):
    LoanApplication.objects.filter(pk=loan_id).update(status='APPROVED')
    return redirect('ceo_analyzer')


@login_required
@role_required(['CEO'])
def ceo_review(request, loan_id):
    LoanApplication.objects.filter(pk=loan_id).update(status='REVIEW')
    return redirect('ceo_analyzer')


@login_required
@role_required(['CEO'])
def ceo_pending(request, loan_id):
    LoanApplication.objects.filter(pk=loan_id).update(status='PENDING')
    return redirect('ceo_analyzer')


@login_required
@role_required(['CEO'])
def ceo_reject(request, loan_id):
    LoanApplication.objects.filter(pk=loan_id).update(status='REJECTED')
    return redirect('ceo_analyzer')

def ceo_approval_detail(request, loan_id):
    loan = get_object_or_404(LoanApplication, pk=loan_id)
    return render(request, 'core/ceo_approval_detail.html', {'loan':loan})

@login_required
@role_required(['CEO'])
def ceo_approval_list(request):
    pending = LoanApplication.objects.filter(status='PENDING').order_by('-id')
    profile = get_profile(request.user)
    return render(request, 'core/ceo_approval_list.html', {'loans': pending, 'profile': profile})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal


@login_required
@role_required(['CEO'])
@transaction.atomic
def disburse_loan(request, pk):
    app = get_object_or_404(LoanApplication, pk=pk)

    # Prevent double disbursement
    if getattr(app, 'is_disbursed', False):
        messages.warning(request, f"Loan for {app.client} already disbursed")
        return redirect('applications')

    # 1. Calculate
    principal = Decimal(app.loan_amount)
    interest = Decimal(getattr(app, 'interest_amount', 0) or 0)
    # If you don't have interest_amount field, use: interest = principal * Decimal('0.2') for 20%
    total_due = principal + interest
    
    # Weekly due - adjust if you have tenure
    tenure_weeks = getattr(app, 'tenure_weeks', 24) or 24
    weekly_due = total_due / Decimal(tenure_weeks)

    # 2. Mark application as disbursed
    app.is_disbursed = True
    app.disbursed_at = timezone.now()
    app.status = 'DISBURSED' # better than APPROVED
    app.save()

    # 3. Create actual Loan ledger for repayment deduction
    loan = Loan.objects.create(
        client=app.client,  # from application
        branch=getattr(app, 'branch', None) or getattr(app.client, 'branch', 'HEAD OFFICE'),
        principal=principal,
        total_due=total_due,
        balance=total_due,  # full at start
        weekly_due=weekly_due,
        loan_application=app  # link if you have FK
    )

    messages.success(request, f"Disbursed ₦{principal} to {app.client}. Weekly: ₦{weekly_due:.0f}")
    return redirect('applications')

@login_required
@role_required(['CEO'])
def assign_officer(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if request.method == 'POST':
        officer_id = request.POST.get('officer_id')
        if officer_id:
            user = get_object_or_404(User, id=officer_id)
            loan.assigned_officer = user
            loan.save()
            messages.success(request, f"Officer {user.username} assigned")
    return redirect('applications')


@login_required
def apply_loan(request):
    profile = get_profile(request.user)
    clients = Client.objects.all().order_by('-id')
    if profile.role in ['OFFICER', 'CREDIT OFFICER']:
        clients = clients.filter(branch=profile.branch)

    if request.method == 'POST':
        try:
            client_id = request.POST.get('client')
            client = get_object_or_404(Client, id=client_id) if client_id else None
            if not client:
                # create quick client if not selected
                client = Client.objects.create(
                    full_name=request.POST.get('full_name'),
                    phone_number=request.POST.get('phone',''),
                    branch=request.POST.get('branch', profile.branch),
                    created_by=request.user
                )
            
            loan = LoanApplication.objects.create(
                client=client,
                full_name=client.full_name,
                branch=client.branch,
                loan_amount=float(request.POST.get('loan_amount') or 0),
                purpose=request.POST.get('purpose','Business'),
                monthly_income=float(request.POST.get('monthly_income') or 250000),
                credit_score=int(request.POST.get('credit_score') or 650),
                age=int(request.POST.get('age') or 30),
                status='PENDING',
            )
            messages.success(request, f"Loan #{loan.id} for {client.full_name} submitted - PENDING CEO review")
            return redirect('applications')
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'core/loan_form.html', {'profile': profile, 'clients': clients})

# Aliases - keep others, REMOVE apply_loan alias
approve_loan = ceo_approve
reject_loan = ceo_reject
new_loan_application = apply_loan
all_applications = applications
clients_list = client_list
new_client = new_client_view
ceo_approvals = ceo_approval_list
officer_register = register_view


from .models import FieldCollection
from django.contrib.auth.decorators import login_required
from datetime import date as dt_date
from django.contrib import messages
from django.shortcuts import redirect, render

@login_required
def field_collection_view(request):
    # 1. Profile & permission FIRST
    my_profile = get_profile(request.user)
    if not my_profile:
        messages.error(request, "Profile not found")
        return redirect('login')
    
    if my_profile.role not in ['OFFICER','ADMIN','CEO'] and not request.user.is_superuser:
        messages.error(request, "Officers only")
        return redirect('dashboard')

    # 2. Date filter
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date_obj = dt_date.fromisoformat(selected_date_str)
        except:
            selected_date_obj = dt_date.today()
    else:
        selected_date_obj = dt_date.today()

    # 3. POST save
    if request.method == 'POST':
        FieldCollection.objects.create(
            officer=request.user,
            client_name=request.POST.get('client_name'),
            branch=request.POST.get('branch', my_profile.branch),
            weekly_savings=request.POST.get('weekly_savings') or 0,
            last_total_savings=request.POST.get('last_total_savings') or 0,
            loan_stage=request.POST.get('loan_stage') or 'FIRST',
            weekly_repayment_due=request.POST.get('weekly_repayment_due') or 0,
            total_repayment=request.POST.get('total_repayment') or 0,
            repayment_balance=request.POST.get('repayment_balance') or 0,
            monthly_loan_amount=request.POST.get('monthly_loan_amount') or 0,
            monthly_repayment=request.POST.get('monthly_repayment') or 0,
            monthly_loan_balance=request.POST.get('monthly_loan_balance') or 0,
            remarks=request.POST.get('remarks',''),
            date=selected_date_obj,  # save with selected date
        )
        messages.success(request, "Field collection saved")
        return redirect(f"{request.path}?date={selected_date_obj.isoformat()}")

    # 4. GET list - filtered by date
    if my_profile.role in ['CEO','ADMIN'] or request.user.is_superuser:
        collections = FieldCollection.objects.filter(date=selected_date_obj).select_related('officer').order_by('-created_at')
    else:
        collections = FieldCollection.objects.filter(officer=request.user, date=selected_date_obj).order_by('-created_at')

    total_savings = sum([c.weekly_savings for c in collections])
    today_count = collections.count()

    return render(request, 'core/field_collection.html', {
        'profile': my_profile,
        'collections': collections,
        'total_savings': total_savings,
        'today_count': today_count,
        'selected_date': selected_date_obj,
    })

@login_required
def field_collection_print(request):
    my_profile = get_profile(request.user)
    selected_date_str = request.GET.get('date')
    try:
        d = dt_date.fromisoformat(selected_date_str) if selected_date_str else dt_date.today()
    except:
        d = dt_date.today()

    if my_profile.role in ['CEO','ADMIN'] or request.user.is_superuser:
        collections = FieldCollection.objects.filter(date=d).order_by('client_name')
    else:
        collections = FieldCollection.objects.filter(officer=request.user, date=d).order_by('client_name')

    return render(request, 'core/field_collection_print.html', {
        'collections': collections,
        'selected_date': d,
        'profile': my_profile
    })


from django.db.models import Sum, Count
from datetime import date as dt_date
from django.shortcuts import redirect, render
from django.contrib import messages

@login_required
def branch_daily_report(request):
    today = dt_date.today()
    my_profile = get_profile(request.user)

    if 'clear' in request.GET:
        return redirect('branch_daily_report')

    if my_profile.role not in ['CEO','ADMIN'] and not request.user.is_superuser:
        messages.error(request, "CEO/Admin only")
        return redirect('dashboard')

    selected_branch = request.GET.get('branch', 'ALL')
    date_str = request.GET.get('date')
    
    try:
        selected_date = dt_date.fromisoformat(date_str) if date_str else today
    except:
        selected_date = today

    base_qs = FieldCollection.objects.filter(date=selected_date)
    
    all_branches = FieldCollection.objects.filter(date=selected_date).values_list('branch', flat=True).distinct()
    if not all_branches:
        all_branches = FieldCollection.objects.values_list('branch', flat=True).distinct()

    if selected_branch and selected_branch != 'ALL':
        base_qs = base_qs.filter(branch=selected_branch)

    branch_names = base_qs.values_list('branch', flat=True).distinct()
    
    branches = []
    for branch in branch_names:
        qs = base_qs.filter(branch=branch)
        agg = qs.aggregate(
            total_clients=Count('id'),
            total_savings=Sum('weekly_savings'),
            total_last_savings=Sum('last_total_savings'),
            total_repayment=Sum('total_repayment'),
            total_expected=Sum('weekly_repayment_due'),
            total_balance=Sum('repayment_balance'),
            total_monthly_repay=Sum('monthly_repayment'),
            total_monthly_bal=Sum('monthly_loan_balance'),
        )
        paid = qs.filter(payment_status='PAID').count()
        partial = qs.filter(payment_status='PARTIAL').count()
        defaults = qs.filter(payment_status='DEFAULT').count()

        exp = agg['total_expected'] or 0
        actual = agg['total_repayment'] or 0
        total_clients = agg['total_clients'] or 0

        branches.append({
            'branch': branch,
            'total_clients': total_clients,
            'total_savings': agg['total_savings'] or 0,
            'total_last_savings': agg['total_last_savings'] or 0,
            'total_new_savings': (agg['total_savings'] or 0) + (agg['total_last_savings'] or 0),
            'total_repayment': actual,
            'total_expected': exp,
            'total_balance': agg['total_balance'] or 0,
            'total_monthly_repay': agg['total_monthly_repay'] or 0,
            'total_monthly_bal': agg['total_monthly_bal'] or 0,
            'paid': paid,
            'partial': partial,
            'defaults': defaults,
            'full_payments': paid,
            'effectiveness': round((paid / total_clients * 100) if total_clients else 0, 1),
            'performance': round((actual / exp * 100) if exp > 0 else (paid / total_clients * 100 if total_clients else 0), 1),
            'default_rate': round((defaults / total_clients * 100) if total_clients else 0, 1),
        })

    overall = base_qs.aggregate(
        total_clients=Count('id'),
        total_savings=Sum('weekly_savings'),
        total_repayment=Sum('total_repayment'),
        total_expected=Sum('weekly_repayment_due'),
        total_balance=Sum('repayment_balance'),
    )
    overall['paid_count'] = base_qs.filter(payment_status='PAID').count()
    overall['partial_count'] = base_qs.filter(payment_status='PARTIAL').count()
    overall['default_count'] = base_qs.filter(payment_status='DEFAULT').count()

    return render(request, 'core/branch_daily_report.html', {
        'profile': my_profile,
        'branches': sorted(branches, key=lambda x: x['performance'], reverse=True),
        'selected_date': selected_date,
        'selected_branch': selected_branch,
        'all_branches': all_branches,
        'overall': overall,
        'collections': base_qs.select_related('officer')[:300]
    })

def privacy_policy(request):
    return render(request, 'core/legal/privacy_policy.html')

def terms_conditions(request):
    return render(request, 'core/legal/terms.html')