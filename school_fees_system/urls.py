"""
URL configuration for school_fees_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from fees import views
from django.contrib.auth import views as auth_views
# UOK Fee Portal Admin Branding
admin.site.site_header = "UOK Fee Portal"
admin.site.site_title = "UOK Fee Portal | Administration"
admin.site.index_title = "University of Kabianga - Administration"
urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('students/register/', views.student_register, name='student_register'),
    path('students/add/', views.register_student, name='register_student'),
    path('students/', views.student_list, name='student_list'),
    path('fees/assign/', views.assign_fee, name='assign_fee'),

    path('fees/', views.fee_list, name='fee_list'),
    path('payments/record/', views.record_payment, name='record_payment'),
    path('payments/', views.payment_list, name='payment_list'),
    path('api/students/', views.student_api, name='student_api'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path(
    'payments/mpesa/',
    views.initiate_mpesa_payment,
    name='initiate_mpesa_payment'
),
path('student/register/', views.student_register, name='student_register'),
path('student/login/', views.student_login, name='student_login'),
path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
path('student/logout/', views.student_logout, name='student_logout'),
path(
    'student/mpesa/',
    views.student_mpesa_payment,
    name='student_mpesa_payment'
),
path(
    'student/receipt/<int:payment_id>/',
    views.student_payment_receipt,
    name='student_payment_receipt'
),
    path(
        'student/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url='/student/password-reset/done/'
        ),
        name='password_reset'
    ),

    path(
        'student/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'student/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'student/reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

