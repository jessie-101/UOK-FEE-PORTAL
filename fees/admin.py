from django.contrib import admin
from .models import Student, Fee, Payment


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'admission_number',
        'first_name',
        'last_name',
        'course',
        'guardian_phone'
    )

    search_fields = (
        'admission_number',
        'first_name',
        'last_name',
        'course'
    )


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'academic_year',
        'semester',
        'amount_due'
    )

    list_filter = ('academic_year', 'semester')

    search_fields = (
        'student__admission_number',
        'student__first_name',
        'student__last_name'
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'fee',
        'amount',
        'payment_method',
        'transaction_reference',
        'status',
        'payment_date'
    )

    list_filter = ('payment_method', 'payment_date', 'status')

    search_fields = (
        'transaction_reference',
        'fee__student__admission_number'
    )