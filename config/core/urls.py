from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('apply/', views.apply_loan, name='apply'),
    path('applications/', views.applications, name='applications'),
    path('approve/<int:pk>/', views.ceo_approve, name='ceo_approve'),
    path('approve/<int:pk>/new/', views.ceo_approve, name='approve_loan'),
    path('reject/<int:pk>/', views.reject_loan, name='reject_loan'),
    path('disburse/<int:pk>/', views.disburse_loan, name='disburse_loan'),
    path('analyzer/', views.analyzer, name='analyzer'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('staff/', views.staff_list_view, name='staff_list'),
    path('staff/<int:user_id>/edit/', views.edit_staff_role, name='edit_staff_role'),
    # Both URLs work for officer registration
    path('register-officer/', views.register_officer, name='register_officer'),
    path('officers/register/', views.register_officer, name='register_officer_alt'),
    path('assign/<int:pk>/', views.assign_officer, name='assign_officer'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)