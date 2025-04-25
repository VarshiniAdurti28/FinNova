from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import OtpVerification, FailedLoginAttempts, PasswordResetRequests, User, Accounts, Transaction
import random
import uuid
import qrcode
import base64
from io import BytesIO
from django.contrib.auth import login, authenticate
from .forms import LoginForm

import pyotp
from .models import CustomerSupportTickets
from django.contrib import messages

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

@csrf_exempt
def support_tickets(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        user = request.user
        user_id = user.user_id

        if message and user_id:
            try:
                CustomerSupportTickets.objects.create(
                    user_id=user_id,
                    message=message,
                    status='open', 
                    created_at=timezone.now()
                )
                messages.success(request, 'Ticket created successfully!')
            except Exception as e:
                messages.error(request, f"Error creating ticket: {e}")
        else:
            messages.error(request, 'Message and User ID are required.')

    tickets = CustomerSupportTickets.objects.all().order_by('-created_at')
    return render(request, 'support_tickets.html', {'tickets': tickets})


def all_transactions(request):
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'all_transactions.html', {'transactions': transactions})

@login_required
def verify_gcode(request):
    if request.method == "POST":
        code = request.POST.get("gcode")
        user = request.user

        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(code):
            request.session['mfa_verified'] = True
            return redirect('/myApp/dashboard')  
        else:
            return render(request, 'mfa_qr.html', {"error": "Invalid code."})
    
    return render(request, 'mfa_qr.html')


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

def generate_dummy_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

def track_failed_login(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return

    now = timezone.now()
    attempt, created = FailedLoginAttempts.objects.get_or_create(user=user)

    if attempt.last_attempt_time and attempt.last_attempt_time.date() == now.date():
        attempt.attempts += 1
    else:
        attempt.attempts = 1

    attempt.last_attempt_time = now
    attempt.save()
    attempt.refresh_from_db()
    if attempt.attempts >= 7:
        handle_suspicious_activity(user)

def login_user(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        print(form)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            print(user)
            if user:
                reset_failed_attempts(user.user_id)
                login(request, user)
                return generate_otp(request)
            else:
                track_failed_login(form.cleaned_data['username'])
                form.add_error(None, "Ooops! Invalid credentials") 
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


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

def code_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generate a random verification code
            verification_code = str(random.randint(100000, 999999))
            # Store the verification code in the user's session
            request.session['verification_code'] = verification_code
            # Send the verification code to the user's email
            send_mail(
                'Verification Code',
                f'Your verification code is: {verification_code}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            # Render the reset password page
            return render(request, 'reset_password.html', {'email': email})
        else:
            return render(request, 'email.html', {'error': 'Invalid email address'})
    else:
        return render(request, 'email.html')

def reset_password_view(request):
    user = request.user
    if request.method == 'POST':
        # dummy_password_input = request.POST.get('dummy_password')
        # new_password = request.POST.get('new_password')
        # confirm_password = request.POST.get('confirm_password')
        # if new_password != confirm_password:
        #     messages.error(request, "New password and confirmation do not match.")
        #     return render(request, 'reset_password.html')
        # if dummy_password_input != "":#user.dummy_password:
        #     messages.error(request, "Invalid dummy password.")
        #     return render(request, 'reset_password.html')
        # user.set_password(new_password)
        # user.dummy_password = None 
        # user.save()
        # update_session_auth_hash(request, user)  
        # messages.success(request, "Your password has been updated successfully!")
        return redirect('dashboard')  
    return render(request, 'index.html')



@login_required
def dashboard(request):
    if request.user.is_authenticated:
        accounts = Accounts.objects.filter(user=request.user)
    else:
        accounts = []
    return render(request, 'index.html', {'accounts':accounts})

@csrf_exempt
def loan_application(request):
    result = None
    if request.method == 'POST':
        try:
            loan = float(request.POST.get('loan_amount'))
            assets = float(request.POST.get('asset_value'))
            income = request.POST.get('income').lower()

            if loan > assets:
                result = {'status': 'denied', 'message': 'Loan denied: amount exceeds asset value.'}
            elif income == 'low' and loan > 1200000:
                result = {'status': 'denied', 'message': 'Loan denied: exceeds limit for low income.'}
            elif income == 'medium' and loan > 5000000:
                result = {'status': 'denied', 'message': 'Loan denied: exceeds limit for medium income.'}
            else:
                result = {'status': 'approved', 'message': 'Loan approved!!'}

        except Exception:
            result = {'status': 'error', 'message': 'Invalid input. Please check your entries.'}

    return render(request, 'loans.html', {'result':result})



@login_required
def emi_calculator(request):
    result = None  
    if request.method == 'POST':
        try:
            loan_amount = float(request.POST.get('loan_amount'))
            annual_rate = float(request.POST.get('annual_rate'))
            tenure_years = int(request.POST.get('tenure_years'))

            monthly_rate = annual_rate / 12 / 100
            total_months = tenure_years * 12

            emi = (loan_amount * monthly_rate * (1 + monthly_rate)**total_months) / \
                  ((1 + monthly_rate)**total_months - 1)
            total_payment = emi * total_months
            total_interest = total_payment - loan_amount

            result = {
                'emi': round(emi, 2),
                'total_payment': round(total_payment, 2),
                'total_interest': round(total_interest, 2)
            }
        except Exception:
            result = {'error': 'Invalid input. Please enter valid numbers.'}

    return render(request, 'emi.html', {'result':result})


