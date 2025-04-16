
from django.contrib import admin
from django.urls import path
from . import views

app_name= 'myApp'
urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('verify_with_otp/', views.otp_verification, name='verify_with_otp'),
    path('resend_otp/', views.generate_otp, name='resend_otp'),
    path('mfa_qr/', views.mfa_qr, name='mfa_qr'),
    path('verify_gcode/', views.verify_gcode, name='verify_gcode'),
    path('trigger_reset/', views.trigger_password_reset, name='trigger_reset'),
    path('reset_password/', views.reset_password_view, name='reset_password'),
    path('loan_application/', views.loan_application, name='loan_application'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('emi_calculator/', views.emi_calculator, name='emi_calculator'),
    # path('loan-request/', views.loan_request, name='loan_request'),

]
