from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('officers/register/', views.register_view, name='officer_register'),
    path('officers/edit/<int:user_id>/', views.edit_staff_role, name='edit_staff_role'),
    path('staff/edit/<int:user_id>/', views.edit_staff_role, name='edit_staff'),
    path('clients/', views.client_list, name='clients_list'),
    path('clients/new/', views.new_client_view, name='new_client'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('applications/', views.applications, name='applications'),
    path('apply/', views.apply_loan, name='apply_loan'),
    path('disburse/<int:pk>/', views.disburse_loan, name='disburse_loan'),

    # CEO APPROVALS
    path('ceo/approvals/', views.ceo_approval_list, name='ceo_approvals'),
    path('ceo/approvals/<int:loan_id>/', views.ceo_approval_detail, name='ceo_approval_detail'),

    # CEO ANALYZER - NEW
    path('ceo/analyzer/', views.ceo_analyzer, name='ceo_analyzer'),
    path('ceo/analyzer/<int:loan_id>/', views.ceo_analyzer, name='ceo_analyze_loan'),

    # CEO ACTIONS - THIS FIXES YOUR ERROR
    path('ceo/approve/<int:loan_id>/', views.ceo_approve, name='ceo_approve'),
    path('ceo/review/<int:loan_id>/', views.ceo_review, name='ceo_review'),
    path('ceo/pending/<int:loan_id>/', views.ceo_pending, name='ceo_pending'),
    path('ceo/reject/<int:loan_id>/', views.ceo_reject, name='ceo_reject'),

    # OLD URLS - ALIAS (prevents 404)
    path('ceo_analyzer/', views.ceo_analyzer, name='ceo_analyzer_old'),
    path('ceo/analyze/', views.ceo_analyzer, name='ceo_analyze_old'),
    path('analyzer/', views.ceo_analyzer, name='analyzer_old'),
]