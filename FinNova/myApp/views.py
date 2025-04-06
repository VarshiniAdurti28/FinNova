from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import OtpVerification
import random
import uuid
import qrcode
import base64
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import LoginForm

import random, string
from django.http import HttpResponse
from django.utils.timezone import now
from django.contrib import messages
from .models import PasswordResetRequests

@login_required
def mfa_qr(request):
    user = request.user  
    if not user.mfa_secret:
        user.generate_mfa_secret()

    otp_uri = user.get_totp_uri()

    qr = qrcode.make(otp_uri)
    
    stream = BytesIO()
    qr.save(stream, format="PNG")
    qr_bytes = stream.getvalue()

    # Convert to Base64
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    return render(request, "mfa_qr.html", {"qr_img": qr_base64})

@login_required
def generate_otp(request):
    otp_code = str(random.randint(100000, 999999))
    expiry_time = now() + timedelta(minutes=5)
    
    OtpVerification.objects.create(user=request.user,  otp_code=otp_code, expiry_time=expiry_time)
    send_mail("Your OTP Code", f"Hello {request.user}, Your OTP is: {otp_code}", "heyyvarshu@gmail.com", [request.user.email])

    return render(request, "otp_verify.html")


@login_required
def otp_verification(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        otp_entry = OtpVerification.objects.filter(user=request.user).last()
        if otp_entry and otp_entry.is_valid() and otp_entry.otp_code == entered_otp:
            print("Otp is correct")
            return redirect("/myApp/mfa_qr/")
        else:
            print("error has occurred")
            return render(request, "otp_verify.html", {"error": "Invalid or expired OTP."})
        
 
    return render(request, "otp_verify.html")

def login_user(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user:
                login(request, user)
                return generate_otp(request)
            else:
                form.add_error(None, "Invalid username or password") 
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def generate_dummy_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@login_required
def trigger_password_reset(request):
    """
    Call this view when the user clicks the reset button on the login page.
    It generates a dummy password, updates the user record, sends an email,
    and then redirects the user to the /reset_password page.
    """
    user = request.user
    dummy_password = generate_dummy_password()
    
    user.set_password(dummy_password)
    user.reset_token = dummy_password
    user.save()

    send_mail(
        subject='Your Password Reset Dummy Password',
        message=f'Use this dummy password to reset your password: {dummy_password}',
        from_email=None, 
        recipient_list=[user.email],
    )
    messages.info(request, "A dummy password has been sent to your email.")
    return redirect('reset_password')


