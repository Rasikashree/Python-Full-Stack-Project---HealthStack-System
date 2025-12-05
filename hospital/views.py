import email
from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, PatientForm, PasswordResetForm
from hospital.models import Hospital_Information, User, Patient 
from doctor.models import Test, testCart, testOrder
from hospital_admin.models import hospital_department, specialization, service, Test_Information
from django.views.decorators.cache import cache_control
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
import datetime
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import searchDoctors, searchHospitals, searchDepartmentDoctors, paginateHospitals
from .models import Patient, User
from doctor.models import Doctor_Information, Appointment,Report, Specimen, Test, Prescription, Prescription_medicine, Prescription_test
from sslcommerz.models import Payment
from django.db.models import Q, Count
import re
from io import BytesIO
from urllib import response
from django.core.mail import BadHeaderError, send_mail
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from doctor.models import Hospital_Department, Specialization, Doctor_Information
from hospital.models import Hospital_Information
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction, IntegrityError

@csrf_exempt
def patient_login(request):
    print("=== LOGIN ATTEMPT ===")
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Username: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # ⭐️ Check if user is a patient ⭐️
            if hasattr(user, 'is_patient') and user.is_patient:
                login(request, user)
                messages.success(request, 'Login successful!')
                
                # Check if it's an AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': 'Login successful!',
                        'redirect_url': '/patient-dashboard/'
                    })
                return redirect('patient-dashboard')
            else:
                # User is not a patient
                messages.error(request, 'This account is not a patient account.')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'error': 'This account is not a patient account.'
                    })
        else:
            messages.error(request, 'Invalid username or password')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid username or password'
                })
    
    return redirect('home')
@csrf_exempt
def patient_register(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not all([first_name, last_name, username, email, password, confirm_password]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'})

        if password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists.'})
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists.'})

        full_name = f"{first_name} {last_name}"

        # Atomic: either both user and patient get created or none
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_patient=True
            )

            # create patient if not exists, otherwise update existing
            try:
                patient, created = Patient.objects.get_or_create(
                    user=user,
                    defaults={'name': full_name}
                )
                if not created:
                    # In case a Patient already exists for this user, update fields
                    patient.name = full_name
                    patient.save()
            except IntegrityError:
                # race: another process created Patient for same user_id -> fetch and update
                patient = Patient.objects.filter(user=user).first()
                if patient:
                    patient.name = full_name
                    patient.save()
                else:
                    # unexpected: rollback by raising so transaction.atomic undoes user creation
                    raise

        return JsonResponse({'success': True, 'message': 'Registration successful! You can now login.'})

    except IntegrityError as e:
        # database constraint error
        return JsonResponse({'success': False, 'message': f'Database error: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if email:
            # Here you could generate a reset link or OTP
            # For now, just simulate success message
            messages.success(request, f"Password reset link sent to {email}")
            return redirect('login')  # redirect to login page
        else:
            messages.error(request, "Please provide a valid email address")
    return render(request, 'hospital/forgot_password.html')

# Create your views here.
@csrf_exempt
def hospital_home(request):
    # .order_by('-created_at')[:6]
    doctors = Doctor_Information.objects.filter(register_status='Accepted')
    hospitals = Hospital_Information.objects.all()
    context = {'doctors': doctors, 'hospitals': hospitals} 
    return render(request, 'index-2.html', context)

@csrf_exempt
@login_required(login_url="login")
def change_password(request,pk):
    patient = Patient.objects.get(user_id=pk)
    context={"patient":patient}
    if request.method == "POST":
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]
        if new_password == confirm_password:
            
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request,"Password Changed Successfully")
            return redirect("patient-dashboard")
        else:
            messages.error(request,"New Password and Confirm Password is not same")
            return redirect("change-password",pk)
    return render(request, 'change-password.html',context)


def add_billing(request):
    return render(request, 'add-billing.html')

def appointments(request):
    return render(request, 'appointments.html')

def edit_billing(request):
    return render(request, 'edit-billing.html')

def edit_prescription(request):
    return render(request, 'edit-prescription.html')

# def forgot_password(request):
#     return render(request, 'forgot-password.html')

@csrf_exempt
def resetPassword(request):
    form = PasswordResetForm()

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user_email = user.email
       
            subject = "Password Reset Requested"
            # email_template_name = "password_reset_email.txt"
            values = {
				"email":user.email,
				'domain':'127.0.0.1:8000',
				'site_name': 'Website',
				"uid": urlsafe_base64_encode(force_bytes(user.pk)),
				"user": user,
				'token': default_token_generator.make_token(user),
				'protocol': 'http',
			}

            html_message = render_to_string('mail_template.html', {'values': values})
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(subject, plain_message, 'admin@example.com',  [user.email], html_message=html_message, fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect ("password_reset_done")

    context = {'form': form}
    return render(request, 'reset_password.html', context)
    
    
def privacy_policy(request):
    return render(request, 'privacy-policy.html')

def about_us(request):
    return render(request, 'about-us.html')

@csrf_exempt
@login_required(login_url="login")
def chat(request, pk):
    patient = Patient.objects.get(user_id=pk)
    doctors = Doctor_Information.objects.all()

    context = {'patient': patient, 'doctors': doctors}
    return render(request, 'chat.html', context)

@csrf_exempt
@login_required(login_url="login")
def chat_doctor(request):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        patients = Patient.objects.all()
        
    context = {'patients': patients, 'doctor': doctor}
    return render(request, 'chat-doctor.html', context)

@csrf_exempt     
@login_required(login_url="login")
def pharmacy_shop(request):
    return render(request, 'pharmacy/shop.html')

@csrf_exempt
def login_user(request):
    if request.method == 'GET':
        return render(request, 'patient-login.html')

    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Username does not exist'
                }, status=400)
            else:
                messages.error(request, 'Username does not exist')
                return render(request, 'patient-login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if user is a patient
            if hasattr(user, "is_patient") and user.is_patient:
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful!',
                        'redirect_url': reverse('patient-dashboard')
                    })
                else:
                    messages.success(request, 'User Logged in Successfully')
                    return redirect('patient-dashboard')
            else:
                logout(request)
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid credentials. Not a Patient'
                    }, status=400)
                else:
                    messages.error(request, 'Invalid credentials. Not a Patient')
                    return redirect('login')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                }, status=400)
            else:
                messages.error(request, 'Invalid username or password')

    # For non-AJAX requests or failed login
    if is_ajax:
        return JsonResponse({
            'success': False,
            'message': 'Login failed'
        }, status=400)
    else:
        return render(request, 'patient-login.html')

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutUser(request):
    logout(request)
    messages.success(request, 'User Logged out')
    return redirect('login')

# @csrf_exempt
# def patient_register(request):
#     page = 'patient-register'
#     form = CustomUserCreationForm()

#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             # form.save()
#             user = form.save(commit=False) # commit=False --> don't save to database yet (we have a chance to modify object)
#             user.is_patient = True
#             # user.username = user.username.lower()  # lowercase username
#             user.save()
#             messages.success(request, 'Patient account was created!')

#             # After user is created, we can log them in --> login(request, user)
#             return redirect('login')

#         else:
#             messages.error(request, 'An error has occurred during registration')

#     context = {'page': page, 'form': form}
#     return render(request, 'patient-register.html', context)

@csrf_exempt
@login_required(login_url="login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def patient_dashboard(request):
    if not request.user.is_patient:
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('logout')
    
    try:
        # This should now always work due to registration fix
        patient = Patient.objects.get(user=request.user)
        report = Report.objects.filter(patient=patient)
        prescription = Prescription.objects.filter(patient=patient).order_by('-prescription_id')
        appointments = Appointment.objects.filter(patient=patient).filter(
            Q(appointment_status='pending') | Q(appointment_status='confirmed')
        )
        payments = Payment.objects.filter(patient=patient).filter(
            appointment__in=appointments
        ).filter(payment_type='appointment').filter(status='VALID')
        
        context = {
            'patient': patient, 
            'appointments': appointments, 
            'payments': payments,
            'report': report,
            'prescription': prescription
        }
        return render(request, 'patient-dashboard.html', context)
        
    except Patient.DoesNotExist:
        # Fallback - create patient record if missing (safety net)
        patient = Patient.objects.create(
            user=request.user,
            name=f"{request.user.first_name} {request.user.last_name}",
            featured_image="default.png"
        )
        messages.info(request, 'Your patient profile has been created.')
        return redirect('patient-dashboard')

# def profile_settings(request):
#     if request.user.is_patient:
#         # patient = Patient.objects.get(user_id=pk)
#         patient = Patient.objects.get(user=request.user)
#         form = PatientForm(instance=patient)  

#         if request.method == 'POST':
#             form = PatientForm(request.POST, request.FILES,instance=patient)  
#             if form.is_valid():
#                 form.save()
#                 return redirect('patient-dashboard')
#             else:
#                 form = PatientForm()
#     else:
#         redirect('logout')

#     context = {'patient': patient, 'form': form}
#     return render(request, 'profile-settings.html', context)

@csrf_exempt
@login_required(login_url="login")
def profile_settings(request):
    if request.user.is_patient:
        # patient = Patient.objects.get(user_id=pk)
        patient = Patient.objects.get(user=request.user)
        old_featured_image = patient.featured_image
        
        if request.method == 'GET':
            context = {'patient': patient}
            return render(request, 'profile-settings.html', context)
        elif request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_featured_image
                
            name = request.POST.get('name')
            dob = request.POST.get('dob')
            age = request.POST.get('age')
            blood_group = request.POST.get('blood_group')
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            nid = request.POST.get('nid')
            history = request.POST.get('history')
            
            patient.name = name
            patient.age = age
            patient.phone_number = phone_number
            patient.address = address
            patient.blood_group = blood_group
            patient.history = history
            patient.dob = dob
            patient.nid = nid
            patient.featured_image = featured_image
            
            patient.save()
            
            messages.success(request, 'Profile Settings Changed!')
            
            return redirect('patient-dashboard')
    else:
        redirect('logout')  
        
def search_doctors(request):
    query = request.GET.get('search_query', '').strip()
    # Pull related FKs to avoid N+1 and ensure fields are present
    doctors = (
        Doctor_Information.objects
        .select_related('department_name', 'specialization', 'hospital_name')
        .filter(register_status='Accepted')
    )

    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) |
            Q(username__icontains=query) |
            Q(department__icontains=query) |
            Q(department_name__hospital_department_name__icontains=query) |
            Q(department_name__name__icontains=query) |
            Q(specialization__specialization_name__icontains=query) |
            Q(hospital_name__name__icontains=query)
        )

    # Deduplicate: show only one card per doctor user (the earliest profile)
    deduped = {}
    for d in doctors.order_by('user_id', 'doctor_id'):
        if d.user_id not in deduped:
            deduped[d.user_id] = d
    doctors = list(deduped.values())

    # Add this to include patient info in sidebar
    patient = Patient.objects.get(user=request.user)

    context = {
        'doctors': doctors,
        'search_query': query,
        'patient': patient,
    }
    return render(request, 'search.html', context)    
    

def checkout_payment(request):
    return render(request, 'checkout.html')

@csrf_exempt
@login_required(login_url="login")
def multiple_hospital(request):
    if request.user.is_authenticated: 
        if request.user.is_patient:
            patient = Patient.objects.get(user=request.user)
            doctors = Doctor_Information.objects.all()
            hospitals = Hospital_Information.objects.all()
            
            hospitals, search_query = searchHospitals(request)

            # Show all hospitals on single page (no pagination)
            context = {'patient': patient, 'doctors': doctors, 'hospitals': hospitals, 'search_query': search_query}
            return render(request, 'multiple-hospital.html', context)
        
        elif request.user.is_doctor:
            # FIX: Use filter().first() instead of get() to handle multiple profiles
            doctor = Doctor_Information.objects.filter(user=request.user).first()
            hospitals = Hospital_Information.objects.all()
            
            hospitals, search_query = searchHospitals(request)

            # Show all hospitals on single page (no pagination)
            context = {'doctor': doctor, 'hospitals': hospitals, 'search_query': search_query}
            return render(request, 'multiple-hospital.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')
    
@csrf_exempt    
@login_required(login_url="login")
def hospital_profile(request, pk):
    if request.user.is_authenticated: 
        if request.user.is_patient:
            patient = Patient.objects.get(user=request.user)
            doctors = Doctor_Information.objects.all()
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
        
            departments = hospital_department.objects.filter(hospital=hospitals)
            specializations = specialization.objects.filter(hospital=hospitals)
            services = service.objects.filter(hospital=hospitals)
            
            context = {'patient': patient, 'doctors': doctors, 'hospitals': hospitals, 'departments': departments, 'specializations': specializations, 'services': services}
            return render(request, 'hospital-profile.html', context)
        
        elif request.user.is_doctor:
            # FIX: Use filter().first() instead of get()
            doctor = Doctor_Information.objects.filter(user=request.user).first()
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
            departments = hospital_department.objects.filter(hospital=hospitals)
            specializations = specialization.objects.filter(hospital=hospitals)
            services = service.objects.filter(hospital=hospitals)
            
            # FIX: Get doctor registrations for this hospital
            doctor_list = Doctor_Information.objects.filter(user=request.user, hospital_name=hospitals)

            context = {
                'doctor': doctor,
                'hospitals': hospitals,
                'departments': departments,
                'specializations': specializations,
                'services': services,
                'doctor_list': doctor_list,
            }
            return render(request, 'hospital-profile.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')
    
    
def data_table(request):
    return render(request, 'data-table.html')

@csrf_exempt
@login_required(login_url="login")
def hospital_department_list(request, pk):
    hospital = get_object_or_404(Hospital_Information, hospital_id=pk)
    departments = hospital_department.objects.filter(hospital=hospital)
    
    # Add proper context for user type
    context = {
        'hospitals': hospital,
        'departments': departments,
    }
    
    # Add user-specific context
    if request.user.is_patient:
        try:
            patient = Patient.objects.get(user=request.user)
            context['patient'] = patient
        except Patient.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
            return redirect('patient-dashboard')
    elif request.user.is_doctor:
        try:
            doctor = Doctor_Information.objects.get(user=request.user)
            context['doctor'] = doctor
        except Doctor_Information.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('doctor-dashboard')
    
    return render(request, 'hospital-department.html', context)

@csrf_exempt
@login_required(login_url="login")
def hospital_doctor_list(request, pk):
    if request.user.is_authenticated and request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        departments = hospital_department.objects.get(hospital_department_id=pk)
        doctors = Doctor_Information.objects.filter(department_name=departments)
        doctors, search_query = searchDepartmentDoctors(request, pk)
        context = {'patient': patient, 'department': departments, 'doctors': doctors, 'search_query': search_query, 'pk_id': pk}
        return render(request, 'hospital-doctor-list.html', context)

    elif request.user.is_authenticated and request.user.is_doctor:
        departments = hospital_department.objects.get(hospital_department_id=pk)
        # FIX: Use filter().first() for current doctor
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        doctor_list = Doctor_Information.objects.filter(user=request.user, department_name=departments)
        doctors = Doctor_Information.objects.filter(department_name=departments)
        doctors, search_query = searchDepartmentDoctors(request, pk)
        context = {
            'doctor': doctor,  # Add this
            'doctor_list': doctor_list, 
            'department': departments, 
            'doctors': doctors, 
            'search_query': search_query, 
            'pk_id': pk
        }
        return render(request, 'hospital-doctor-list.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')
    
@csrf_exempt
@login_required(login_url="login")
def hospital_doctor_register(request, pk):
    hospital = get_object_or_404(Hospital_Information, hospital_id=pk)
    departments = hospital_department.objects.filter(hospital=hospital)
    specializations = specialization.objects.filter(hospital=hospital)

    # SAFE APPROACH: Use filter().first() instead of get()
    current_doctor = Doctor_Information.objects.filter(user=request.user).first()
    doctor_list = Doctor_Information.objects.filter(user=request.user, hospital_name=hospital)
    already_registered = doctor_list.exists()

    if request.method == "POST":
        department_id = request.POST.get("department_radio")
        specialization_id = request.POST.get("specialization_radio")
        certificate = request.FILES.get("certificate_image")

        if not all([department_id, specialization_id, certificate]):
            messages.error(request, "All fields are required.")
            return redirect('hospital-doctor-register', pk=hospital.hospital_id)

        try:
            department = hospital_department.objects.get(pk=department_id)
            specialization_obj = specialization.objects.get(pk=specialization_id)
        except (hospital_department.DoesNotExist, specialization.DoesNotExist):
            messages.error(request, "Invalid selection.")
            return redirect('hospital-doctor-register', pk=hospital.hospital_id)

        existing_registration = doctor_list.first()
        
        if existing_registration:
            if existing_registration.register_status == 'Rejected':
                existing_registration.register_status = 'Pending'
                existing_registration.department_name = department
                existing_registration.specialization = specialization_obj
                existing_registration.certificate_image = certificate
                existing_registration.save()
                messages.success(request, "Application resubmitted successfully!")
            else:
                messages.info(request, f"You already have a {existing_registration.register_status.lower()} application.")
        else:
            Doctor_Information.objects.create(
                user=request.user,
                hospital_name=hospital,
                department_name=department,
                specialization=specialization_obj,
                certificate_image=certificate,
                register_status='Pending',
                name=current_doctor.name if current_doctor else f"{request.user.first_name} {request.user.last_name}"
            )
            messages.success(request, "Application submitted successfully!")

        return redirect('hospital-doctor-register', pk=hospital.hospital_id)

    context = {
        'hospitals': hospital,
        'departments': departments,
        'specializations': specializations,
        'already_registered': already_registered,
        'doctor': current_doctor,
        'doctor_list': doctor_list,
    }
    return render(request, 'hospital-doctor-register.html', context)
   
def testing(request):
    # hospitals = Hospital_Information.objects.get(hospital_id=1)
    test = "test"
    context = {'test': test}
    return render(request, 'testing.html', context)

@csrf_exempt
@login_required(login_url="login")
def view_report(request,pk):
    if request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        report = Report.objects.filter(report_id=pk)
        specimen = Specimen.objects.filter(report__in=report)
        test = Test.objects.filter(report__in=report)

        # current_date = datetime.date.today()
        context = {'patient':patient,'report':report,'test':test,'specimen':specimen}
        return render(request, 'view-report.html',context)
    else:
        redirect('logout') 


def test_cart(request):
    return render(request, 'test-cart.html')

@csrf_exempt
@login_required(login_url="login")
def test_single(request,pk):
     if request.user.is_authenticated and request.user.is_patient:
         
        patient = Patient.objects.get(user=request.user)
        Perscription_test = Perscription_test.objects.get(test_id=pk)
        carts = testCart.objects.filter(user=request.user, purchased=False)
        
        context = {'patient': patient, 'carts': carts, 'Perscription_test': Perscription_test}
        return render(request, 'test-cart.html',context)
     else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html')  

@csrf_exempt
@login_required(login_url="login")
def test_add_to_cart(request, pk, pk2):
    if request.user.is_authenticated and request.user.is_patient:
         
        patient = Patient.objects.get(user=request.user)
        test_information = Test_Information.objects.get(test_id=pk2)
        prescription = Prescription.objects.filter(prescription_id=pk)

        item = get_object_or_404(Prescription_test, test_info_id=pk2,prescription_id=pk)
        order_item = testCart.objects.get_or_create(item=item, user=request.user, purchased=False)
        order_qs = testOrder.objects.filter(user=request.user, ordered=False)

        if order_qs.exists():
            order = order_qs[0]
            order.orderitems.add(order_item[0])
            # messages.info(request, "This test is added to your cart!")
            return redirect("prescription-view", pk=pk)
        else:
            order = testOrder(user=request.user)
            order.save()
            order.orderitems.add(order_item[0])
            return redirect("prescription-view", pk=pk)

        context = {'patient': patient,'prescription_test': prescription_tests,'prescription':prescription,'prescription_medicine':prescription_medicine,'test_information':test_information}
        return render(request, 'prescription-view.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html')  

@csrf_exempt
@login_required(login_url="login")
def test_cart(request, pk):
    if request.user.is_authenticated and request.user is patient:
        # prescription = Prescription.objects.filter(prescription_id=pk)
        
        prescription = Prescription.objects.filter(prescription_id=pk)
        
        patient = Patient.objects.get(user=request.user)
        prescription_test = Prescription_test.objects.all()
        test_carts = testCart.objects.filter(user=request.user, purchased=False)
        test_orders = testOrder.objects.filter(user=request.user, ordered=False)
        
        if test_carts.exists() and test_orders.exists():
            test_order = test_orders[0]
            
            context = {'test_carts': test_carts,'test_order': test_order, 'patient': patient, 'prescription_test':prescription_test, 'prescription_id':pk}
            return render(request, 'test-cart.html', context)
        else:
            # messages.warning(request, "You don't have any test in your cart!")
            context = {'patient': patient,'prescription_test':prescription_test}
            return render(request, 'prescription-view.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html') 

@csrf_exempt
@login_required(login_url="login")
def test_remove_cart(request, pk):
    if request.user.is_authenticated and request.user.is_patient:
        item = Prescription_test.objects.get(test_id=pk)

        patient = Patient.objects.get(user=request.user)
        prescription = Prescription.objects.filter(prescription_id=pk)
        prescription_medicine = Prescription_medicine.objects.filter(prescription__in=prescription)
        prescription_test = Prescription_test.objects.filter(prescription__in=prescription)
        test_carts = testCart.objects.filter(user=request.user, purchased=False)
        
        # item = get_object_or_404(test, pk=pk)
        test_order_qs = testOrder.objects.filter(user=request.user, ordered=False)
        if test_order_qs.exists():
            test_order = test_order_qs[0]
            if test_order.orderitems.filter(item=item).exists():
                test_order_item = testCart.objects.filter(item=item, user=request.user, purchased=False)[0]
                test_order.orderitems.remove(test_order_item)
                test_order_item.delete()
                # messages.warning(request, "This test was remove from your cart!")
                context = {'test_carts': test_carts,'test_order': test_order,'patient': patient,'prescription_id':pk}
                return render(request, 'test-cart.html', context)
            else:
                # messages.info(request, "This test was not in your cart")
                context = {'patient': patient,'test': item,'prescription':prescription,'prescription_medicine':prescription_medicine,'prescription_test':prescription_test}
                return render(request, 'prescription-view.html', context)
        else:
            # messages.info(request, "You don't have an active order")
            context = {'patient': patient,'test': item,'prescription':prescription,'prescription_medicine':prescription_medicine,'prescription_test':prescription_test}
            return redirect('prescription-view', pk=prescription.prescription_id)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html') 

@csrf_exempt
def prescription_view(request,pk):
      if request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        prescription = Prescription.objects.filter(prescription_id=pk)
        prescription_medicine = Prescription_medicine.objects.filter(prescription__in=prescription)
        prescription_test = Prescription_test.objects.filter(prescription__in=prescription)

        context = {'patient':patient,'prescription':prescription,'prescription_test':prescription_test,'prescription_medicine':prescription_medicine}
        return render(request, 'prescription-view.html',context)
      else:
         redirect('logout') 

@csrf_exempt
def render_to_pdf(template_src, context_dict={}):
    template=get_template(template_src)
    html=template.render(context_dict)
    result=BytesIO()
    pres_pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pres_pdf.err:
        return HttpResponse(result.getvalue(),content_type="aplication/pres_pdf")
    return None


# def prescription_pdf(request,pk):
#  if request.user.is_patient:
#     patient = Patient.objects.get(user=request.user)
#     prescription = Prescription.objects.get(prescription_id=pk)
#     perscription_medicine = Perscription_medicine.objects.filter(prescription=prescription)
#     perscription_test = Perscription_test.objects.filter(prescription=prescription)
#     current_date = datetime.date.today()
#     context={'patient':patient,'current_date' : current_date,'prescription':prescription,'perscription_test':perscription_test,'perscription_medicine':perscription_medicine}
#     pdf=render_to_pdf('prescription_pdf.html', context)
#     if pdf:
#         response=HttpResponse(pdf, content_type='application/pdf')
#         content="inline; filename=report.pdf"
#         # response['Content-Disposition']= content
#         return response
#     return HttpResponse("Not Found")

@csrf_exempt
def prescription_pdf(request,pk):
 if request.user.is_patient:
    patient = Patient.objects.get(user=request.user)
    prescription = Prescription.objects.get(prescription_id=pk)
    prescription_medicine = Prescription_medicine.objects.filter(prescription=prescription)
    prescription_test = Prescription_test.objects.filter(prescription=prescription)
    # current_date = datetime.date.today()
    context={'patient':patient,'prescription':prescription,'prescription_test':prescription_test,'prescription_medicine':prescription_medicine}
    pres_pdf=render_to_pdf('prescription_pdf.html', context)
    if pres_pdf:
        response=HttpResponse(pres_pdf, content_type='application/pres_pdf')
        content="inline; filename=prescription.pdf"
        response['Content-Disposition']= content
        return response
    return HttpResponse("Not Found")

@csrf_exempt
@login_required(login_url="login")
def delete_prescription(request,pk):
    if request.user.is_authenticated and request.user.is_patient:
        prescription = Prescription.objects.get(prescription_id=pk)
        prescription.delete()
        messages.success(request, 'Prescription Deleted')
        return redirect('patient-dashboard')
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')

@csrf_exempt
@login_required(login_url="login")
def delete_report(request,pk):
    if request.user.is_authenticated and request.user.is_patient:
        report = Report.objects.get(report_id=pk)
        report.delete()
        messages.success(request, 'Report Deleted')
        return redirect('patient-dashboard')
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')

@csrf_exempt
@receiver(user_logged_in)
def got_online(sender, user, request, **kwargs):    
    user.login_status = True
    user.save()

@csrf_exempt
@receiver(user_logged_out)
def got_offline(sender, user, request, **kwargs):   
    user.login_status = False
    user.save()

from doctor.models import Doctor_Information
from django.shortcuts import redirect, get_object_or_404

def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor_Information, pk=doctor_id)
    doctor.delete()
    return redirect('register-doctor-list')



