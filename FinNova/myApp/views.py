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
from django.contrib.auth import update_session_auth_hash
from django.db import connection

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
                track_failed_login(username)
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
    return redirect('reset_password')

@login_required
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
    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM myApp_user WHERE username = %s", [username])
        row = cursor.fetchone()
        if not row:
            return  
        user_id = row[0]
        cursor.execute("""
            SELECT attempt_id, attempts, last_attempt 
            FROM myApp_failedloginattempts 
            WHERE user_id = %s 
            ORDER BY last_attempt DESC LIMIT 1
        """, [user_id])
        record = cursor.fetchone()
        now = timezone.now()
        if record:
            attempt_id, attempts, last_attempt = record
            if last_attempt.date() == now.date():
                attempts += 1
                cursor.execute("""
                    UPDATE myApp_failedloginattempts 
                    SET attempts = %s, last_attempt = %s 
                    WHERE attempt_id = %s
                """, [attempts, now, attempt_id])
            else:
                attempts = 1   
                cursor.execute("""
                    INSERT INTO myApp_failedloginattempts (user_id, attempts, last_attempt)
                    VALUES (%s, %s, %s)
                """, [user_id, attempts, now])
        else:
            cursor.execute("""
                INSERT INTO myApp_failedloginattempts (user_id, attempts, last_attempt)
                VALUES (%s, %s, %s)
            """, [user_id, 1, now])
        if attempts >= 7:
            handle_suspicious_activity(user_id)
            
def reset_failed_attempts(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE myApp_failedloginattempts 
            SET attempts = 0 
            WHERE user_id = %s
        """, [user_id])
        
def handle_suspicious_activity(user_id):
    dummy_password = generate_dummy_password()
    with connection.cursor() as cursor:
        cursor.execute("SELECT email, username FROM myApp_user WHERE user_id = %s", [user_id])
        result = cursor.fetchone()
        if not result:
            return
        email, username = result
        from django.contrib.auth.hashers import make_password
        hashed = make_password(dummy_password)
        cursor.execute("""
            UPDATE myApp_user 
            SET password_hash = %s 
            WHERE user_id = %s
        """, [hashed, user_id])
        send_mail(
            subject="FinNova: Suspicious Login Attempt Detected",
            message=f"Hi {username},\n\nWe detected multiple failed login attempts to your account. Your password has been reset as a security measure.\n\nTemporary Password: {dummy_password}\n\nPlease login and change it immediately.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email]
        )
