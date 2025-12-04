from django.db import models
import uuid
from django.conf import settings


# import django user model
from django.contrib.auth.models import AbstractUser
from django import forms
from django.http import JsonResponse

class PatientRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        if User.objects.filter(username=cleaned_data.get('username')).exists():
            raise forms.ValidationError("Username already exists.")
        
        if User.objects.filter(email=cleaned_data.get('email')).exists():
            raise forms.ValidationError("Email already exists.")
        
        return cleaned_data

# def patient_register(request):
#     if request.method == 'POST':
#         form = PatientRegistrationForm(request.POST)
        
#         if form.is_valid():
#             try:
#                 user = User.objects.create_user(
#                     username=form.cleaned_data['username'],
#                     email=form.cleaned_data['email'],
#                     password=form.cleaned_data['password'],
#                     first_name=form.cleaned_data['first_name'],
#                     last_name=form.cleaned_data['last_name']
#                 )
                
#                 return JsonResponse({
#                     'success': True,
#                     'message': 'Registration successful!'
#                 })
                
#             except Exception as e:
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Error creating user: {str(e)}'
#                 })
#         else:
#             # Return form errors
#             errors = {field: error.get_json_data() for field, error in form.errors.items()}
#             return JsonResponse({
#                 'success': False,
#                 'message': 'Please correct the errors below.',
#                 'errors': errors
#             })
    
#     return JsonResponse({
#         'success': False,
#         'message': 'Invalid request method.'
#     })

# Create your models here.

"""
null=True --> don't require a value when inserting into the database
blank=True --> allow blank value when submitting a form
auto_now_add --> automatically set the value to the current date and time
unique=True --> prevent duplicate values
primary_key=True --> set this field as the primary key
editable=False --> prevent the user from editing this field

django field types --> google it  # every field types has field options
Django automatically creates id field for each model class which will be a PK # primary_key=True --> if u want to set manual
"""

class User(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_hospital_admin = models.BooleanField(default=False)
    is_labworker = models.BooleanField(default=False)
    is_pharmacist = models.BooleanField(default=False)
    #login_status = models.CharField(max_length=200, null=True, blank=True, default="offline")
    login_status = models.BooleanField(default=False)
    
class Hospital_Information(models.Model):
    HOSPITAL_TYPE = (
        ('private', 'Private hospital'),
        ('public', 'Public hospital'),
    )

    hospital_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    featured_image = models.ImageField(upload_to='doctor_images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    phone_number = models.BigIntegerField(null=True, blank=True)
    hospital_type = models.CharField(max_length=200, choices=HOSPITAL_TYPE)
    general_bed_no = models.IntegerField(null=True, blank=True)
    available_icu_no = models.IntegerField(null=True, blank=True)
    regular_cabin_no = models.IntegerField(null=True, blank=True)
    emergency_cabin_no = models.IntegerField(null=True, blank=True)
    vip_cabin_no = models.IntegerField(null=True, blank=True)

    
    def __str__(self):
        return str(self.name)
        
class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='patient')
    name = models.CharField(max_length=200, null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    featured_image = models.ImageField(upload_to='patients/', default='patients/user-default.png', null=True, blank=True)
    blood_group = models.CharField(max_length=200, null=True, blank=True)
    history = models.CharField(max_length=200, null=True, blank=True)
    dob = models.CharField(max_length=200, null=True, blank=True)
    nid = models.CharField(max_length=200, null=True, blank=True)
    serial_number = models.CharField(max_length=200, null=True, blank=True)
    
    # Chat login status
    login_status = models.CharField(max_length=200, null=True, blank=True, default="offline")

    def __str__(self):
        return str(self.user.username) if self.user else "No User"

class DoctorPrescription(models.Model):
    prescription_id = models.AutoField(primary_key=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_prescriptions')
    prescription_text = models.TextField()
    extra_information = models.TextField(null=True, blank=True)  # <-- this must exist
    created_at = models.DateTimeField(auto_now_add=True)

