from django.contrib import admin

# Register your models here.
from .models import Subject, Transaction, Record

admin.site.register(Subject)
admin.site.register(Transaction)
admin.site.register(Record)
