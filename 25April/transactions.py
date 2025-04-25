#In models.py
from django.db import models

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
    ]

    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.date} - {self.amount} - {self.status}"

#Run migrations
#python manage.py makemigrations
#python manage.py migrate

#In views.py
from django.shortcuts import render
from .models import Transaction

def all_transactions(request):
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'all_transactions.html', {'transactions': transactions})

#In  your apps.url.py
from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.all_transactions, name='all_transactions'),
]

#And in your main urls.py (project-level):
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('yourapp.urls')),  # replace 'yourapp' with the actual app name
]
#save the html code  all_transactions.html in
#yourapp/templates/all_transactions.html
