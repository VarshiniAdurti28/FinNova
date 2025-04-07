from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import OtpVerification, FailedLoginAttempts, PasswordResetRequests, User
import random
import uuid
import qrcode
import base64
from io import BytesIO
from django.contrib.auth import login, authenticate
from .forms import LoginForm

import random, string
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import connection

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import os
import json
from django.utils import timezone
from django.db.models import F

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
                reset_failed_attempts(user.id)
                login(request, user)
                return generate_otp(request)
            else:
                track_failed_login(form.cleaned_data['username'])
                form.add_error(None, "Ooops! Invalid credentials") 
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
    return redirect('myApp:reset_password')

def reset_password_view(request):
    user = request.user
    if request.method == 'POST':
        dummy_password_input = request.POST.get('dummy_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return render(request, 'reset_password.html')
        if dummy_password_input != user.dummy_password:
            messages.error(request, "Invalid dummy password.")
            return render(request, 'reset_password.html')
        user.set_password(new_password)
        user.dummy_password = None 
        user.save()
        update_session_auth_hash(request, user)  
        messages.success(request, "Your password has been updated successfully!")
        return redirect('dashboard')  
    return render(request, 'reset_password.html')



def track_failed_login(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return

    now = timezone.now()
    attempt, created = FailedLoginAttempts.objects.get_or_create(user=user)

    if attempt.last_attempt_time and attempt.last_attempt_time.date() == now.date():
        attempt.attempts = F('attempts') + 1
    else:
        attempt.attempts = 1

    attempt.last_attempt_time = now
    attempt.save()
    attempt.refresh_from_db()
    if attempt.attempts >= 7:
        handle_suspicious_activity(user)

            
def reset_failed_attempts(user_id):
    FailedLoginAttempts.objects.filter(user_id=user_id).update(attempts=0)

def handle_suspicious_activity(user):
    dummy_password = generate_dummy_password()
    user.set_password(dummy_password)
    user.save()

    send_mail(
        subject="FinNova: Suspicious Login Attempt Detected",
        message=f"Hi {user.username},\n\nWe detected multiple failed login attempts to your account. Your password has been reset.\n\nTemporary Password: {dummy_password}\n\nPlease login and change it immediately.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email]
    )


def serve_form(request):
    file_path = os.path.join(settings.BASE_DIR, 'loans.html')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='text/html')
    return HttpResponse("File not found", status=404)

@csrf_exempt
@require_POST
def loan_request(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        loan = data.get('loanAmount')
        assets = data.get('assetValue')
        income = data.get('income')

        if loan is None or assets is None or not income:
            return JsonResponse({'success': False, 'message': 'Invalid input'}, status=400)

        if loan > assets:
            return JsonResponse({'success': False, 'message': 'Loan denied: amount exceeds asset value.'})

        if income == 'low' and loan > 1200000:
            return JsonResponse({'success': False, 'message': 'Loan denied: exceeds limit for low income.'})
        elif income == 'medium' and loan > 5000000:
            return JsonResponse({'success': False, 'message': 'Loan denied: exceeds limit for medium income.'})

        return JsonResponse({'success': True, 'message': 'Loan approved!!'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)

