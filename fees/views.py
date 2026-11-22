import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth import (
    get_user_model,
    authenticate,
    login,
    logout
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Student, Fee, Payment
from .forms import (
    StudentForm,
    StudentRegistrationForm,
    FeeForm,
    PaymentForm,
    MpesaPaymentForm
)
from .mpesa import stk_push
from .serializers import StudentSerializer


# HOME PAGE
def home(request):
    context = {
        'total_students': Student.objects.count(),
        'total_fees': Fee.objects.count(),
        'total_payments': Payment.objects.filter(
            status='Completed'
        ).count(),
    }

    return render(request, 'fees/home.html', context)


# STUDENT SELF-REGISTRATION
def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            User = get_user_model()

            admission_number = form.cleaned_data['admission_number']
            password = form.cleaned_data['password']

            try:
                with transaction.atomic():
                    student = Student.objects.select_for_update().get(
                        admission_number=admission_number,
                        user__isnull=True
                    )

                    user = User.objects.create_user(
                        username=admission_number,
                        password=password,
                        first_name=student.first_name,
                        last_name=student.last_name
                    )

                    student.user = user
                    student.save(update_fields=['user'])

                messages.success(
                    request,
                    'Registration successful. You can now log in.'
                )

                return redirect('student_login')

            except Exception:
                form.add_error(
                    None,
                    'Registration failed. Please check your details or contact the fees office.'
                )

    else:
        form = StudentRegistrationForm()

    return render(request, 'fees/student_register.html', {
        'form': form
    })


# STUDENT LOGIN
def student_login(request):
    if request.method == 'POST':
        admission_number = request.POST.get(
            'admission_number', ''
        ).strip()

        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=admission_number,
            password=password
        )

        if user is not None:
            if hasattr(user, 'student_profile'):
                login(request, user)
                return redirect('student_dashboard')

        messages.error(
            request,
            'Invalid admission number or password.'
        )

    return render(request, 'fees/student_login.html')


# STUDENT LOGOUT
@login_required
def student_logout(request):
    logout(request)
    return redirect('student_login')


# STUDENT DASHBOARD
@login_required
def student_dashboard(request):
    try:
        student = request.user.student_profile

    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        logout(request)
        return redirect('student_login')

    fees = Fee.objects.filter(
        student=student
    ).prefetch_related('payments')

    payments = Payment.objects.filter(
        fee__student=student
    ).select_related('fee').order_by('-payment_date')

    total_due = sum(fee.amount_due for fee in fees)
    total_paid = sum(fee.total_paid for fee in fees)
    balance = total_due - total_paid

    context = {
        'student': student,
        'fees': fees,
        'payments': payments,
        'total_due': total_due,
        'total_paid': total_paid,
        'balance': balance,
    }

    return render(
        request,
        'fees/student_dashboard.html',
        context
    )


# ADMIN: REGISTER STUDENT
@staff_member_required
def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            User = get_user_model()

            try:
                with transaction.atomic():
                    admission_number = form.cleaned_data['admission_number']

                    user = User.objects.create_user(
                        username=admission_number,
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name']
                    )

                    Student.objects.create(
                        admission_number=admission_number,
                        user=user,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        course=form.cleaned_data['course'],
                        guardian_phone=form.cleaned_data['guardian_phone']
                    )

                messages.success(
                    request,
                    'Registration successful. You can now log in.'
                )
                return redirect('student_login')

            except Exception:
                form.add_error(
                    None,
                    'Registration failed. Please check your details and try again.'
                )

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        'fees/student_register.html',
        {'form': form}
    )


# ADMIN: STUDENT LIST
@staff_member_required
def student_list(request):
    search_query = request.GET.get('search', '')

    students = Student.objects.all().order_by(
        'admission_number'
    )

    if search_query:
        students = students.filter(
            models.Q(admission_number__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )

    students = students.prefetch_related('fees__payments')

    return render(
        request,
        'fees/student_list.html',
        {
            'students': students,
            'search_query': search_query
        }
    )


# ADMIN: ASSIGN FEES
@staff_member_required
def assign_fee(request):
    if request.method == 'POST':
        form = FeeForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('fee_list')

    else:
        form = FeeForm()

    return render(
        request,
        'fees/assign_fee.html',
        {'form': form}
    )


# ADMIN: FEE LIST
@staff_member_required
def fee_list(request):
    fees = Fee.objects.select_related(
        'student'
    ).all().order_by(
        'academic_year',
        'semester'
    )

    return render(
        request,
        'fees/fee_list.html',
        {'fees': fees}
    )


# ADMIN: RECORD PAYMENT
@staff_member_required
def record_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('payment_list')

    else:
        form = PaymentForm()

    return render(
        request,
        'fees/record_payment.html',
        {'form': form}
    )


# ADMIN: INITIATE M-PESA PAYMENT
@staff_member_required
def initiate_mpesa_payment(request):
    if request.method == 'POST':
        print("MPESA VIEW RECEIVED:", request.method)

        form = MpesaPaymentForm(request.POST)

        if form.is_valid():
            fee = form.cleaned_data['fee']
            amount = form.cleaned_data['amount']
            phone_number = form.cleaned_data['phone_number']

            payment = Payment.objects.create(
                fee=fee,
                amount=amount,
                payment_method='M-Pesa',
                status='Pending'
            )

            callback_url = os.getenv('MPESA_CALLBACK_URL')

            print("MPESA CALLBACK URL:", callback_url)

            try:
                response = stk_push(
                    phone_number=phone_number,
                    amount=int(amount),
                    callback_url=callback_url,
                    account_reference=fee.student.admission_number
                )

                print("MPESA RESPONSE:", response)

                checkout_id = response.get('CheckoutRequestID')

                if response.get('ResponseCode') == '0' and checkout_id:
                    payment.checkout_request_id = checkout_id
                    payment.save()

                    return render(
                        request,
                        'fees/mpesa_payment.html',
                        {
                            'message': (
                                'M-Pesa payment request sent. '
                                'Check your phone and enter your M-Pesa PIN.'
                            ),
                            'payment': payment
                        }
                    )

                payment.status = 'Failed'
                payment.save()

                form.add_error(
                    None,
                    response.get(
                        'ResponseDescription',
                        'M-Pesa request was unsuccessful.'
                    )
                )

            except Exception as e:
                print("MPESA ERROR:", repr(e))

                payment.status = 'Failed'
                payment.save()

                form.add_error(
                    None,
                    'Unable to initiate M-Pesa payment. Please try again.'
                )

        else:
            print("MPESA FORM ERRORS:", form.errors)

    else:
        form = MpesaPaymentForm()

    return render(
        request,
        'fees/mpesa_payment.html',
        {'form': form}
    )


# ADMIN: PAYMENT LIST
@staff_member_required
def payment_list(request):
    payments = Payment.objects.select_related(
        'fee__student'
    ).all().order_by('-payment_date')

    return render(
        request,
        'fees/payment_list.html',
        {'payments': payments}
    )


# STUDENT: INITIATE M-PESA PAYMENT
@login_required(login_url='student_login')
def student_mpesa_payment(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_login')

    form = MpesaPaymentForm(request.POST or None)

    form.fields['fee'].queryset = Fee.objects.filter(
        student=student
    )

    if request.method == 'POST':
        if form.is_valid():
            fee = form.cleaned_data['fee']
            amount = form.cleaned_data['amount']
            phone_number = form.cleaned_data['phone_number']

            payment = Payment.objects.create(
                fee=fee,
                amount=amount,
                payment_method='M-Pesa',
                status='Pending'
            )

            callback_url = os.getenv('MPESA_CALLBACK_URL')

            try:
                response = stk_push(
                    phone_number=phone_number,
                    amount=int(amount),
                    callback_url=callback_url,
                    account_reference=student.admission_number
                )

                checkout_id = response.get('CheckoutRequestID')

                if response.get('ResponseCode') == '0' and checkout_id:
                    payment.checkout_request_id = checkout_id
                    payment.save()

                    return render(
                        request,
                        'fees/mpesa_payment.html',
                        {
                            'message': (
                                'M-Pesa request sent. Check your phone '
                                'and enter your M-Pesa PIN.'
                            ),
                            'payment': payment
                        }
                    )

                payment.status = 'Failed'
                payment.save()

                form.add_error(
                    None,
                    response.get(
                        'ResponseDescription',
                        'M-Pesa request was unsuccessful.'
                    )
                )

            except Exception as e:
                print("STUDENT MPESA ERROR:", repr(e))

                payment.status = 'Failed'
                payment.save()

                form.add_error(
                    None,
                    'Unable to initiate M-Pesa payment. Please try again.'
                )

    return render(
        request,
        'fees/mpesa_payment.html',
        {'form': form}
    )


# STUDENT PAYMENT RECEIPT
@login_required(login_url='student_login')
def student_payment_receipt(request, payment_id):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_login')

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        fee__student=student,
        status='Completed'
    )

    return render(
        request,
        'fees/student_receipt.html',
        {'payment': payment, 'student': student}
    )


# M-PESA CALLBACK
@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        data = json.loads(request.body)

        callback = data['Body']['stkCallback']

        checkout_request_id = callback.get(
            'CheckoutRequestID'
        )

        if not checkout_request_id:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': 'Missing checkout ID'
            })

        result_code = callback.get('ResultCode')

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                checkout_request_id=checkout_request_id
            )

            if payment.status != 'Pending':
                return JsonResponse({
                    'ResultCode': 0,
                    'ResultDesc': 'Callback already processed'
                })

            if result_code == 0:
                metadata = callback.get(
                    'CallbackMetadata', {}
                ).get('Item', [])

                receipt_number = None

                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value')
                        break

                if not receipt_number:
                    return JsonResponse({
                        'ResultCode': 1,
                        'ResultDesc': 'Missing M-Pesa receipt number'
                    })

                payment.transaction_reference = receipt_number
                payment.status = 'Completed'

            else:
                payment.status = 'Failed'

            payment.save()

        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Callback processed successfully'
        })

    except Payment.DoesNotExist:
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Payment not found'
        })

    except (
        KeyError,
        ValueError,
        TypeError,
        json.JSONDecodeError
    ):
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Invalid callback data'
        })


# ADMIN: STUDENT API
@staff_member_required
@api_view(['GET', 'POST'])
def student_api(request):
    if request.method == 'GET':
        students = Student.objects.all()

        serializer = StudentSerializer(
            students,
            many=True
        )

        return Response(serializer.data)

    serializer = StudentSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)