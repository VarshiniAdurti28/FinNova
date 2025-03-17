
from django.contrib import admin
from django.urls import path
from . import views

app_name= 'myApp'
urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('verify_with_otp/', views.otp_verification, name='verify_with_otp'),
    path('resend_otp/', views.generate_otp, name='resend_otp'),
    path('mfa_qr/', views.mfa_qr, name='mfa_qr'),

]
