from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Student, Fee, Payment


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'admission_number',
            'first_name',
            'last_name',
            'course',
            'guardian_phone'
        ]

class StudentRegistrationForm(forms.Form):
    admission_number = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    course = forms.CharField(max_length=150)
    guardian_phone = forms.CharField(max_length=20)

    password = forms.CharField(
        widget=forms.PasswordInput(),
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
    )

    def clean_admission_number(self):
        admission_number = self.cleaned_data['admission_number'].strip()

        if Student.objects.filter(admission_number=admission_number).exists():
            raise forms.ValidationError(
                "This admission number is already registered. Please log in or contact the fees office."
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        if User.objects.filter(username=admission_number).exists():
            raise forms.ValidationError(
                "An account with this admission number already exists. Please log in."
            )

        return admission_number

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error(
                'confirm_password',
                "Passwords do not match."
            )

        return cleaned_data

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = [
            'student',
            'academic_year',
            'semester',
            'amount_due'
        ]
        widgets = {
            'academic_year': forms.TextInput(attrs={
                'placeholder': 'e.g. 2026/2027'
            }),
            'amount_due': forms.NumberInput(attrs={
                'placeholder': 'Enter amount due',
                'min': '0.01',
                'step': '0.01'
            }),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'fee',
            'amount',
            'payment_method',
            'transaction_reference'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Enter payment amount',
                'min': '0.01',
                'step': '0.01'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'placeholder': 'Enter transaction reference'
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        fee = self.cleaned_data['fee']

        if amount <= 0:
            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )

        if amount > fee.balance:
            raise forms.ValidationError(
                "Payment amount cannot exceed the outstanding balance."
            )

        return amount


class MpesaPaymentForm(forms.Form):
    fee = forms.ModelChoiceField(
        queryset=Fee.objects.select_related('student').all(),
        label="Select Fee"
    )

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Amount to Pay",
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter amount',
            'min': '0.01',
            'step': '0.01'
        })
    )

    phone_number = forms.CharField(
        max_length=13,
        label="M-Pesa Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 0712345678'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        fee = cleaned_data.get('fee')
        amount = cleaned_data.get('amount')

        if fee and amount and amount > fee.balance:
            self.add_error(
                'amount',
                "Amount cannot exceed the outstanding fee balance."
            )

        return cleaned_data

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()

        if phone.startswith('+254'):
            phone = phone[1:]

        if phone.startswith('0'):
            phone = '254' + phone[1:]

        if len(phone) != 12 or not phone.isdigit() or not phone.startswith('254'):
            raise forms.ValidationError(
                "Enter a valid Kenyan phone number, e.g. 0712345678."
            )

        return phone