from django.db import models
from django.db.models import Sum
from django.conf import settings


class Student(models.Model):
    admission_number = models.CharField(max_length=30, unique=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"


class Fee(models.Model):
    SEMESTER_CHOICES = [
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fees'
    )

    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'semester'],
                name='unique_student_fee_per_semester'
            )
        ]

    @property
    def total_paid(self):
        result = self.payments.filter(
            status='Completed'
        ).aggregate(total=Sum('amount'))

        return result['total'] or 0

    @property
    def balance(self):
        return self.amount_due - self.total_paid

    def __str__(self):
        return f"{self.student} - {self.academic_year} - {self.semester}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('M-Pesa', 'M-Pesa'),
        ('Bank', 'Bank'),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    checkout_request_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='Completed'
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fee.student} - KSh {self.amount}"