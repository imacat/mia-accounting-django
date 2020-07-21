from django.contrib import admin

# Register your models here.
from .models import Account, Transaction, Record

admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Record)
