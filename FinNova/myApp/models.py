# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils.timezone import now
import pyotp
import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class Accounts(models.Model):
    account_id = models.AutoField(primary_key=True)
    account_number = models.CharField(unique=True, max_length=20)
    account_type = models.CharField(max_length=8)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey('User', models.DO_NOTHING)


class Admins(models.Model):
    admin_id = models.AutoField(primary_key=True)
    admin_username = models.CharField(unique=True, max_length=50)
    admin_password_hash = models.CharField(max_length=256)
    role = models.ForeignKey('AdminRolePermissions', models.DO_NOTHING)


class AdminActions(models.Model):
    action_id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(Admins, models.DO_NOTHING)
    action_type = models.CharField(max_length=19)
    details = models.TextField()
    performed_at = models.DateTimeField(blank=True, null=True)

  
class AdminRolePermissions(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=19)
    can_manage_User = models.IntegerField(blank=True, null=True)
    can_approve_loans = models.IntegerField(blank=True, null=True)
    can_review_transactions = models.IntegerField(blank=True, null=True)
    can_handle_support_tickets = models.IntegerField(blank=True, null=True)

class ChapChallengeRequests(models.Model):
    challenge_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    challenge = models.CharField(max_length=256)
    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9, blank=True, null=True)



class ChapResponses(models.Model):
    response_id = models.AutoField(primary_key=True)
    challenge = models.ForeignKey(ChapChallengeRequests, models.DO_NOTHING)
    user = models.ForeignKey('User', models.DO_NOTHING)
    response_hash = models.CharField(max_length=256)
    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)


class CustomerSupportTickets(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    message = models.TextField()
    status = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)\
    



class FailedLoginAttempts(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    attempts = models.IntegerField(blank=True, null=True)
    last_attempt_time = models.DateTimeField(blank=True, null=True)


class FraudDetectionLogs(models.Model):
    transaction = models.ForeignKey('Transactions', models.DO_NOTHING)
    log_id = models.AutoField(primary_key=True)
    flagged_reason = models.TextField()
    flagged_at = models.DateTimeField(blank=True, null=True)



class LoanApplications(models.Model):
    loan_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Accounts, models.DO_NOTHING)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    loan_term = models.IntegerField()
    status = models.CharField(max_length=8, blank=True, null=True)
    application_date = models.DateTimeField(blank=True, null=True)



class LoanRepayments(models.Model):
    loan = models.ForeignKey(LoanApplications, models.DO_NOTHING)
    repayment_id = models.AutoField(primary_key=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    repayment_date = models.DateTimeField(blank=True, null=True)




class OtpVerification(models.Model):
    user = models.ForeignKey('User', models.DO_NOTHING)
    otp_id = models.AutoField(primary_key=True)
    otp_code = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()

    def is_valid(self):
        return self.expiry_time > now()
    


class PasswordResetRequests(models.Model):
    reset_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    reset_token = models.CharField(unique=True, max_length=255)
    expiry_time = models.DateTimeField()


class SuspiciousAdminActivities(models.Model):
    suspicious_id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(Admins, models.DO_NOTHING)
    activity_description = models.TextField()
    flagged_at = models.DateTimeField(blank=True, null=True)

class Transactions(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    sender_account = models.ForeignKey(Accounts, models.DO_NOTHING, db_column='sender_account')
    receiver_account = models.ForeignKey(Accounts, models.DO_NOTHING, db_column='receiver_account', related_name='transactions_receiver_account_set')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=7, blank=True, null=True)


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=50, blank=False)
    password = models.CharField(max_length=256)
    email = models.CharField(unique=True, max_length=100, blank=False)
    created_at = models.DateTimeField(blank=True, null=True)
    mfa_secret = models.CharField(max_length=50, blank=True, null=True)  
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()  
    USERNAME_FIELD = 'username' 
    REQUIRED_FIELDS = ['email'] 

    def generate_mfa_secret(self):
        secret = pyotp.random_base32() 
        self.mfa_secret = secret
        self.save()
        return secret

    def get_totp_uri(self):
        return f"otpauth://totp/FinNova:{self.username}?secret={self.mfa_secret}&issuer=FinNova"
    
    
