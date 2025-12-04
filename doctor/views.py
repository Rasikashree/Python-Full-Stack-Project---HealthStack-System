import email
from email import message
from multiprocessing import context
from turtle import title
from django.shortcuts import render, redirect
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from hospital_admin.views import prescription_list
from .forms import DoctorUserCreationForm, DoctorForm
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_control
from hospital.models import User, Patient, Hospital_Information
from django.apps import apps
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# Resolve Appointment model dynamically (some projects place it in a different app)
Appointment = None
for app_label in ('hospital', 'hospital_admin', 'doctor', 'appointments'):
    try:
        Appointment = apps.get_model(app_label, 'Appointment')
        if Appointment is not None:
            break
    except LookupError:
        continue

if Appointment is None:
    raise ImportError(
        "Appointment model not found. Search your project for 'class Appointment' and update the import "
        "or add its app label to the resolver list in doctor/views.py"
    )

from hospital_admin.models import Admin_Information,Clinical_Laboratory_Technician
from .models import Doctor_Information, Education, Experience, Prescription_medicine, Report,Specimen,Test, Prescription_test, Prescription, Doctor_review
from hospital_admin.models import Admin_Information,Clinical_Laboratory_Technician, Test_Information
from .models import Doctor_Information, Education, Experience, Prescription_medicine, Report,Specimen,Test, Prescription_test, Prescription
from django.db.models import Q, Count
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
import json
import random
import string
from datetime import datetime, timedelta
import datetime
import re
from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.html import strip_tags
from io import BytesIO
from urllib import response
from django.shortcuts import render
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import Report
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Doctor_Information

# Create your views here.

def generate_random_string():
    N = 8
    string_var = ""
    string_var = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=N))
    return string_var

@csrf_exempt
@login_required(login_url="doctor-login")
def doctor_change_password(request,pk):
    doctor = Doctor_Information.objects.filter(user_id=pk).first()    
    context={'doctor':doctor}
    if request.method == "POST":
        
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]
        if new_password == confirm_password:
            
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request,"Password Changed Successfully")
            update_session_auth_hash(request, request.user)
            return redirect("doctor-dashboard")
            
        else:
            messages.error(request,"New Password and Confirm Password is not same")
            return redirect("change-password",pk)
        
    return render(request, 'doctor-change-password.html',context)

@csrf_exempt
@login_required(login_url="doctor-login")
def schedule_timings(request):
    doctor = Doctor_Information.objects.filter(user=request.user).first()
    context = {'doctor': doctor}
    
    return render(request, 'schedule-timings.html', context)

@csrf_exempt
@login_required(login_url="doctor-login")
def patient_id(request):
    return render(request, 'patient-id.html')

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutDoctor(request):
    user = User.objects.get(id=request.user.id)
    if user.is_doctor:
        user.login_status = "offline"
        user.save()
        logout(request)
    
    messages.success(request, 'User Logged out')
    return render(request,'doctor-login.html')

def doctor_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")



@csrf_exempt
def doctor_register(request):
    if request.method == 'GET':
        form = DoctorUserCreationForm()
        return render(request, 'doctor-register.html', {'form': form})

    # POST: use Django form validation
    form = DoctorUserCreationForm(request.POST)

    # Pre-check for common duplicates to provide clear feedback
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    if username and User.objects.filter(username__iexact=username).exists():
        messages.error(request, 'Doctor account already exists.')
        return render(request, 'doctor-register.html', {'form': form})
    if email and User.objects.filter(email__iexact=email).exists():
        messages.error(request, 'An account with this email already exists.')
        return render(request, 'doctor-register.html', {'form': form})
    if not form.is_valid():
        # Show concise, user-friendly messages for common cases
        error_text = None
        if 'username' in form.errors:
            for err in form.errors['username']:
                if 'already exists' in err.lower():
                    error_text = 'Doctor account already exists.'
                    break
        if not error_text:
            # Fallback to first validation error without dumping all fields
            # Prefer a single clear message
            first_field, first_errors = next(iter(form.errors.items()))
            error_text = first_errors[0]
        messages.error(request, error_text)
        return render(request, 'doctor-register.html', {'form': form})

    # Create user via form and mark as doctor
    user = form.save(commit=False)
    user.is_doctor = True
    user.save()

    # Auto-login and redirect appropriately
    login(request, user)
    # Ensure a Doctor_Information profile exists to avoid template reverse errors
    # Pick a default hospital to satisfy NOT NULL constraint
    default_hospital = Hospital_Information.objects.first()
    if default_hospital is None:
        default_hospital = Hospital_Information.objects.create(name='Default Hospital')
    doctor, _created = Doctor_Information.objects.get_or_create(
        user=user,
        defaults={
            'username': user.username,
            'email': user.email,
            'hospital_name': default_hospital,
        }
    )
    messages.success(request, 'Doctor login created successfully.')
    return redirect('doctor-dashboard')

@csrf_exempt
def doctor_login(request):
    # page = 'patient_login'
    if request.method == 'GET':
        return render(request, 'doctor-login.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')
                
        user = authenticate(username=username, password=password)
        
        if user is not None:
            
            login(request, user)
            if request.user.is_doctor:
                # user.login_status = "online"
                # user.save()
                messages.success(request, 'Welcome Doctor!')
                return redirect('doctor-dashboard')
            else:
                messages.error(request, 'Invalid credentials. Not a Doctor')
                return redirect('doctor-logout')   
        else:
            messages.error(request, 'Invalid username or password')

            
            
    return render(request, 'doctor-login.html')

@csrf_exempt
@login_required(login_url="doctor-login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doctor_dashboard(request):
    if request.user.is_authenticated and request.user.is_doctor:
        # Gather all profiles for this doctor user (some users may have multiple hospital registrations)
        doctors_qs = Doctor_Information.objects.filter(user=request.user)
        if not doctors_qs.exists():
            default_hospital = Hospital_Information.objects.first()
            if default_hospital is None:
                default_hospital = Hospital_Information.objects.create(name='Default Hospital')
            created_doc, _ = Doctor_Information.objects.get_or_create(
                user=request.user,
                defaults={
                    'username': request.user.username,
                    'email': request.user.email,
                    'hospital_name': default_hospital,
                }
            )
            doctors_qs = Doctor_Information.objects.filter(pk=created_doc.pk)
        
        current_date = datetime.date.today()
        # Today list: include both pending and confirmed so the doctor sees new bookings
        today_appointments = Appointment.objects.filter(
            date=current_date, doctor__in=doctors_qs
        ).filter(
            Q(appointment_status='pending') | Q(appointment_status='confirmed')
        ).order_by('time')

        # Next day metrics
        next_date = current_date + datetime.timedelta(days=1)
        next_days_appointment = Appointment.objects.filter(
            date=next_date, doctor__in=doctors_qs
        ).filter(
            Q(appointment_status='pending') | Q(appointment_status='confirmed')
        ).count()

        # Simple integer counts for widgets
        today_patient_count = Appointment.objects.filter(
            date=current_date, doctor__in=doctors_qs
        ).count()

        total_appointments_count = Appointment.objects.filter(
            doctor__in=doctors_qs
        ).count()
        
        context = {
            'doctor': doctors_qs.first(),
            'today_appointments': today_appointments,
            'today_patient_count': today_patient_count,
            'total_appointments_count': total_appointments_count,
            'next_days_appointment': next_days_appointment,
            'current_date': current_date.strftime('%Y-%m-%d'),
            'next_date': next_date.strftime('%Y-%m-%d')
        }
        return render(request, 'doctor-dashboard.html', context)
    else:
        return redirect('doctor-login')
 
@csrf_exempt
@login_required(login_url="doctor-login")
def appointments(request):
    try:
        # Get all doctor profiles for this user
        doctors_qs = Doctor_Information.objects.filter(user=request.user)
        if not doctors_qs.exists():
            messages.error(request, "Doctor profile not found")
            return redirect('doctor-login')
            
        appointments = Appointment.objects.filter(doctor__in=doctors_qs).filter(appointment_status='pending').order_by('date')
        context = {'doctor': doctors_qs.first(), 'appointments': appointments}
        return render(request, 'appointments.html', context)
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor-dashboard')
 

@csrf_exempt
def book_appointment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        doctor_id = data.get('doctor_id')
        date = data.get('date')
        time = data.get('time')
        appointment_type = data.get('appointment_type', 'checkup')
        message = data.get('message', '')
        patient = Patient.objects.get(user=request.user)
        doctor = Doctor_Information.objects.get(pk=doctor_id)
        serial_number = generate_random_string()
        # Idempotent create: avoid duplicate rows for the same slot
        appt, created = Appointment.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            date=date,
            time=time,
            defaults={
                'appointment_type': appointment_type,
                'appointment_status': 'pending',
                'serial_number': serial_number,
                'message': message
            }
        )
        return JsonResponse({'success': True, 'appointment_id': appt.id, 'created': created})
    return JsonResponse({'success': False})


@csrf_exempt        
@login_required(login_url="doctor-login")
def accept_appointment(request, pk):
    try:
        # Must own the appointment via any of your doctor profiles
        appointment = get_object_or_404(Appointment, id=pk, doctor__user=request.user)
        appointment.appointment_status = 'confirmed'
        appointment.save()
        
        messages.success(request, 'Appointment Accepted Successfully')
        return redirect('doctor-dashboard')
        
    except Exception as e:
        messages.error(request, f'Error accepting appointment: {str(e)}')
        return redirect('appointments')

@csrf_exempt
@login_required(login_url="doctor-login")
def reject_appointment(request, pk):
    try:
        appointment = get_object_or_404(Appointment, id=pk, doctor__user=request.user)
        appointment.appointment_status = 'cancelled'
        appointment.save()
        
        messages.success(request, 'Appointment Rejected Successfully')
        return redirect('doctor-dashboard')
        
    except Exception as e:
        messages.error(request, f'Error rejecting appointment: {str(e)}')
        return redirect('appointments')

#         end_year = doctor.end_year
#         end_year = re.sub("'", "", end_year)
#         end_year = end_year.replace("[", "")
#         end_year = end_year.replace("]", "")
#         end_year = end_year.replace(",", "")
#         end_year_array = end_year.split()       
#         experience = zip(work_place_array, designation_array, start_year_array, end_year_array)

@csrf_exempt
@login_required(login_url="doctor-login")
def doctor_profile(request, pk):
    doctor = get_object_or_404(Doctor_Information, pk=pk)
    context = {'doctor': doctor}
    return render(request, 'doctor-profile.html', context)

def get_doctor_list(request):
    """
    Get list of all registered doctors for chatbot/patient views.
    Returns JSON with: id, name, department_name, specialization_name,
    hospital_name, hospital_address, featured_image, consultation_fee.
    """
    print("=== DEBUG: Starting get_doctor_list ===")
    try:
        # Only list registered/accepted doctors; select related for efficiency
        base_qs = Doctor_Information.objects.all()
        if hasattr(Doctor_Information, 'register_status'):
            base_qs = base_qs.filter(register_status='Accepted')
        # If an is_active flag exists, respect it too
        if hasattr(Doctor_Information, 'is_active'):
            base_qs = base_qs.filter(is_active=True)

        qs = base_qs.select_related('hospital_name', 'specialization', 'department_name')
        doctors = []
        for d in qs:
            # department_name may be a related object or a simple field on model.
            dept_name = ''
            # try a few common attribute names safely
            if hasattr(d, 'department_name') and d.department_name:
                # Prefer the pure department field if available on related model
                dept_name = getattr(d.department_name, 'hospital_department_name', None) or str(d.department_name)
            elif hasattr(d, 'department') and d.department:
                # if department is a FK object, try to get a name attribute
                dept_obj = getattr(d, 'department')
                dept_name = getattr(dept_obj, 'name', str(dept_obj))
            # specialization name if available
            spec_name = ''
            try:
                if getattr(d, 'specialization', None):
                    spec_name = getattr(d.specialization, 'specialization_name', '')
            except Exception:
                spec_name = ''
            # hospital details if available
            hosp_name = ''
            hosp_addr = ''
            try:
                if getattr(d, 'hospital_name', None):
                    hosp_name = getattr(d.hospital_name, 'name', '') or ''
                    hosp_addr = getattr(d.hospital_name, 'address', '') or ''
            except Exception:
                hosp_name = ''
                hosp_addr = ''
            # featured image url if available
            featured = ''
            try:
                featured = d.featured_image.url if getattr(d, 'featured_image', None) else ''
            except Exception:
                featured = ''
            doctors.append({
                'id': d.pk,
                'name': getattr(d, 'name', '') or getattr(d, 'full_name', '') or '',
                'department_name': dept_name,
                'specialization_name': spec_name,
                'hospital_name': hosp_name,
                'hospital_address': hosp_addr,
                'featured_image': featured,
                'consultation_fee': getattr(d, 'consultation_fee', None),
            })
            print(f"=== DEBUG: Added doctor {getattr(d,'name','<unknown>')} (ID: {d.pk}) ===")
        print(f"=== DEBUG: Returning {len(doctors)} doctors ===")
        return JsonResponse({'success': True, 'doctors': doctors})
    except Exception as e:
        print("=== DEBUG: Error in get_doctor_list:", str(e), "===")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required(login_url="doctor-login")
def delete_education(request, pk):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        
        educations = Education.objects.get(education_id=pk)
        educations.delete()
        
        messages.success(request, 'Education Deleted')
        return redirect('doctor-profile-settings')

@csrf_exempt  
@login_required(login_url="doctor-login")
def delete_experience(request, pk):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        
        experiences = Experience.objects.get(experience_id=pk)
        experiences.delete()
        
        messages.success(request, 'Experience Deleted')
        return redirect('doctor-profile-settings')
      
@csrf_exempt      
@login_required(login_url="doctor-login")
def doctor_profile_settings(request, pk):
    doctor = get_object_or_404(Doctor_Information, pk=pk)
    if request.method == "POST":
        # update fields as before
        doctor.name = request.POST.get("name")
        doctor.phone_number = request.POST.get("number")
        doctor.gender = request.POST.get("gender")
        doctor.dob = request.POST.get("dob")
        doctor.nid = request.POST.get("nid")
        doctor.visiting_hour = request.POST.get("visit_hour")
        doctor.description = request.POST.get("description")
        doctor.consultation_fee = request.POST.get("consultation_fee")
        doctor.report_fee = request.POST.get("report_fee")
        if request.FILES.get("featured_image"):
            doctor.featured_image = request.FILES["featured_image"]
        doctor.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("doctor-profile-settings", pk=pk)
    context = {'doctor': doctor}
    return render(request, "doctor-profile-settings.html", context)
    # profile_Settings.js
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        old_featured_image = doctor.featured_image
        

        if request.method == 'GET':
            educations = Education.objects.filter(doctor=doctor)
            experiences = Experience.objects.filter(doctor=doctor)
                    
            context = {'doctor': doctor, 'educations': educations, 'experiences': experiences}
            return render(request, 'doctor-profile-settings.html', context)
        elif request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_featured_image
                
            name = request.POST.get('name')
            number = request.POST.get('number')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            description = request.POST.get('description')
            consultation_fee = request.POST.get('consultation_fee')
            report_fee = request.POST.get('report_fee')
            nid = request.POST.get('nid')
            visit_hour = request.POST.get('visit_hour')
            
            degree = request.POST.getlist('degree')
            institute = request.POST.getlist('institute')
            year_complete = request.POST.getlist('year_complete')
            hospital_name = request.POST.getlist('hospital_name')     
            start_year= request.POST.getlist('from')
            end_year = request.POST.getlist('to')
            designation = request.POST.getlist('designation')

            doctor.name = name
            doctor.visiting_hour = visit_hour
            doctor.nid = nid
            doctor.gender = gender
            doctor.featured_image = featured_image
            doctor.phone_number = number
            #doctor.visiting_hour
            doctor.consultation_fee = consultation_fee
            doctor.report_fee = report_fee
            doctor.description = description
            doctor.dob = dob
            
            doctor.save()
            
            # Education
            for i in range(len(degree)):
                education = Education(doctor=doctor)
                education.degree = degree[i]
                education.institute = institute[i]
                education.year_of_completion = year_complete[i]
                education.save()

            # Experience
            for i in range(len(hospital_name)):
                experience = Experience(doctor=doctor)
                experience.work_place_name = hospital_name[i]
                experience.from_year = start_year[i]
                experience.to_year = end_year[i]
                experience.designation = designation[i]
                experience.save()
      
            # context = {'degree': degree}
            messages.success(request, 'Profile Updated')
            return redirect('doctor-dashboard')
    else:
        redirect('doctor-logout')
               

@csrf_exempt
@login_required(login_url="patient-login")
def book_appointment(request):
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                doctor_id = data.get('doctor_id')
                date = data.get('date')
                time = data.get('time')
                appointment_type = data.get('appointment_type', 'checkup')
                message = data.get('message', '')
            else:
                # Handle form data from regular booking
                doctor_id = request.POST.get('doctor_id')
                date = request.POST.get('date')
                time = request.POST.get('time')
                appointment_type = request.POST.get('appointment_type', 'checkup')
                message = request.POST.get('message', '')
            
            # Validate required fields
            if not all([doctor_id, date, time]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            try:
                patient = Patient.objects.get(user=request.user)
                doctor = Doctor_Information.objects.get(pk=doctor_id)
            except Patient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Patient profile not found'})
            except Doctor_Information.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Doctor not found'})
            
            # Generate serial number
            serial_number = generate_random_string()
            
            # Idempotent create: avoid duplicate rows for the same slot
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                date=date,
                time=time,
                defaults={
                    'appointment_type': appointment_type,
                    'appointment_status': 'pending',
                    'serial_number': serial_number,
                    'message': message
                }
            )
            
            return JsonResponse({
                'success': True, 
                'appointment_id': appointment.id,
                'message': 'Appointment booked successfully',
                'serial_number': getattr(appointment, 'serial_number', serial_number),
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Add this new view specifically for chatbot appointments
@csrf_exempt
@login_required(login_url="patient-login")
def book_appointment_chatbot(request):
    """
    Accepts JSON POST from chatbot and creates an Appointment.
    Expects: { doctor_id, date (YYYY-MM-DD), time (HH:MM or string), appointment_type }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        doctor_id = payload.get('doctor_id')
        date = payload.get('date')
        time_val = payload.get('time')
        appointment_type = payload.get('appointment_type', 'checkup')

        if not (doctor_id and date and time_val):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)

        doctor = get_object_or_404(Doctor_Information, pk=doctor_id)

        # try to resolve a Patient instance linked to the logged-in user
        patient_obj = None
        try:
            patient_obj = Patient.objects.filter(user=request.user).first()
        except Exception:
            patient_obj = None

        # Create appointment - adapt fields if your model is different
        appt_kwargs = {
            'doctor': doctor,
            'date': date,
            'time': time_val,
            'appointment_type': appointment_type,
            'appointment_status': 'pending'
        }

        # If Appointment model expects a patient FK named 'patient', set it
        if 'patient' in [f.name for f in Appointment._meta.fields]:
            if patient_obj:
                appt_kwargs['patient'] = patient_obj
            else:
                # if the model uses a user FK or different name, attempt best-effort
                if 'user' in [f.name for f in Appointment._meta.fields]:
                    appt_kwargs['user'] = request.user

        # Idempotent create for chatbot as well
        lookup = {k: v for k, v in appt_kwargs.items() if k in ('doctor','date','time')}
        appointment, created = Appointment.objects.get_or_create(
            **lookup,
            defaults=appt_kwargs
        )

        # Construct a serial_number to return if model doesn't provide one
        serial_number = getattr(appointment, 'serial_number', None) or f"APPT{appointment.pk:06d}"

        return JsonResponse({'success': True, 'appointment_id': appointment.pk, 'serial_number': serial_number, 'created': created})
    except Exception as e:
        print("=== DEBUG: Error in book_appointment_chatbot:", str(e), "===")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt    
@login_required(login_url="doctor-login")      
def booking_success(request):
    return render(request, 'booking-success.html')

@csrf_exempt
@login_required(login_url="doctor-login")
def booking(request, pk):
    patient = request.user.patient
    doctor = Doctor_Information.objects.get(doctor_id=pk)

    if request.method == 'POST':
        appointment = Appointment(patient=patient, doctor=doctor)
        date = request.POST['appoint_date']
        time = request.POST['appoint_time']
        appointment_type = request.POST['appointment_type']
        message = request.POST['message']

        transformed_date = datetime.datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        transformed_date = str(transformed_date)
         
        appointment.date = transformed_date
        appointment.time = time
        appointment.appointment_status = 'pending'
        appointment.serial_number = generate_random_string()
        appointment.appointment_type = appointment_type
        appointment.message = message
        appointment.save()
        
        # REMOVED EMAIL CODE - No email sending for booking
        
        messages.success(request, 'Appointment Booked Successfully')
        return redirect('patient-dashboard')

    context = {'patient': patient, 'doctor': doctor}
    return render(request, 'booking.html', context)

@csrf_exempt
@login_required(login_url="doctor-login")
def my_patients(request):
    if request.user.is_doctor:
        doctors_qs = Doctor_Information.objects.filter(user=request.user)
        # return unique patients who have confirmed appointments with any of this user's doctor profiles
        patients = Patient.objects.filter(appointment__doctor__in=doctors_qs, appointment__appointment_status='confirmed').distinct()
    else:
        return redirect('doctor-logout')

    context = {'doctor': doctors_qs.first(), 'patients': patients}
    return render(request, 'my-patients.html', context)


# def patient_profile(request):
#     return render(request, 'patient_profile.html')

@csrf_exempt
@login_required(login_url="doctor-login")
def patient_profile(request, pk):
    if request.user.is_doctor:
        doctors_qs = Doctor_Information.objects.filter(user=request.user)
        patient = get_object_or_404(Patient, patient_id=pk)
        appointments = Appointment.objects.filter(doctor__in=doctors_qs, patient=patient)
        prescription = Prescription.objects.filter(doctor__in=doctors_qs, patient=patient)
        report = Report.objects.filter(doctor__in=doctors_qs, patient=patient)
    else:
        redirect('doctor-logout')
    context = {'doctor': doctors_qs.first(), 'appointments': appointments, 'patient': patient, 'prescription': prescription, 'report': report}  
    return render(request, 'patient-profile.html', context)



@csrf_exempt
@login_required(login_url="doctor-login")
def create_prescription(request, pk):
    if request.user.is_doctor:
        # A doctor user may have multiple Doctor_Information rows; use the first
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        if not doctor:
            messages.error(request, 'Doctor profile not found')
            return redirect('doctor-dashboard')
        patient = get_object_or_404(Patient, patient_id=pk)
        create_date = datetime.date.today()

        if request.method == 'POST':
            prescription = Prescription(doctor=doctor, patient=patient)

            test_name = request.POST.getlist('test_name')
            test_description = request.POST.getlist('description')
            medicine_name = request.POST.getlist('medicine_name')
            medicine_quantity = request.POST.getlist('quantity')
            medecine_frequency = request.POST.getlist('frequency')
            medicine_duration = request.POST.getlist('duration')
            medicine_relation_with_meal = request.POST.getlist('relation_with_meal')
            medicine_instruction = request.POST.getlist('instruction')
            extra_information = request.POST.get('extra_information')
            test_info_ids = request.POST.getlist('id')

            prescription.extra_information = extra_information
            prescription.create_date = create_date
            prescription.save()

            # Save medicines
            for i in range(len(medicine_name)):
                medicine = Prescription_medicine(prescription=prescription)
                medicine.medicine_name = medicine_name[i]
                medicine.quantity = medicine_quantity[i]
                medicine.frequency = medecine_frequency[i]
                medicine.duration = medicine_duration[i]
                medicine.instruction = medicine_instruction[i]
                medicine.relation_with_meal = medicine_relation_with_meal[i]
                medicine.save()

            # Save tests safely
            for i in range(len(test_name)):
                if test_info_ids[i]:  # Only process if ID is not empty
                    tests = Prescription_test(prescription=prescription)
                    tests.test_name = test_name[i]
                    tests.test_description = test_description[i]
                    tests.test_info_id = test_info_ids[i]

                    try:
                        test_info = Test_Information.objects.get(test_id=int(test_info_ids[i]))
                        tests.test_info_price = test_info.test_price
                    except (ValueError, Test_Information.DoesNotExist):
                        tests.test_info_price = 0  # default price if ID invalid

                    tests.save()

            messages.success(request, 'Prescription Created')
            return redirect('patient-profile', pk=patient.patient_id)

        context = {'doctor': doctor, 'patient': patient}
        return render(request, 'create-prescription.html', context)
    
    
@csrf_exempt      
def render_to_pdf(template_src, context_dict={}):
    template=get_template(template_src)
    html=template.render(context_dict)
    result=BytesIO()
    pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")

    return None

@csrf_exempt
def report_pdf(request, pk):
 if request.user.is_patient:
    patient = Patient.objects.get(user=request.user)
    report = Report.objects.get(report_id=pk)
    specimen = Specimen.objects.filter(report=report)
    test = Test.objects.filter(report=report)
    # current_date = datetime.date.today()
    context={'patient':patient,'report':report,'test':test,'specimen':specimen}
    pdf=render_to_pdf('report_pdf.html', context)
    if pdf:
        response=HttpResponse(pdf, content_type='application/pdf')
        content="inline; filename=report.pdf"
        # response['Content-Disposition']= content
        return response
    return HttpResponse("Not Found")

def download_report_pdf(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # Example: just returning a simple PDF
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, f"Report for Patient: {patient.name}")
    p.drawString(100, 730, f"Patient ID: {patient.patient_id}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

# def testing(request):
#     doctor = Doctor_Information.objects.filter(user=request.user).first()
#     degree = doctor.degree
#     degree = re.sub("'", "", degree)
#     degree = degree.replace("[", "")
#     degree = degree.replace("]", "")
#     degree = degree.replace(",", "")
#     degree_array = degree.split()
    
#     education = zip(degree_array, institute_array)
    
#     context = {'doctor': doctor, 'degree': institute, 'institute_array': institute_array, 'education': education}
#     # test range, len, and loop to show variables before moving on to doctor profile
    
#     return render(request, 'testing.html', context)
@csrf_exempt
@login_required(login_url="login")
def patient_search(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = get_object_or_404(Doctor_Information, doctor_id=pk)
        query = request.GET.get("search_query", "").strip()
        patient = None
        prescriptions = None

        if query:
            if query.isdigit():  
                patient = Patient.objects.filter(patient_id=int(query)).first()
            else:
                patient = Patient.objects.filter(name__icontains=query).first()

            if patient:
                prescriptions = Prescription.objects.filter(doctor=doctor, patient=patient)

        context = {
            'patient': patient,
            'doctor': doctor,
            'prescription': prescriptions
        }

        return render(request, 'patient-profile.html', context)

    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return redirect('doctor-login')
    
@csrf_exempt
@login_required(login_url="login")
def doctor_test_list(request):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        tests = Test_Information.objects.all()
        context = {'doctor': doctor, 'tests': tests}
        return render(request, 'doctor-test-list.html', context)
    
    elif request.user.is_authenticated and request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        tests = Test_Information.objects.all()
        context = {'patient': patient, 'tests': tests}
        return render(request, 'doctor-test-list.html', context)
        
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'doctor-login.html')


@csrf_exempt
@login_required(login_url="login")
def doctor_view_prescription(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        prescriptions = Prescription.objects.get(prescription_id=pk)
        medicines = Prescription_medicine.objects.filter(prescription=prescriptions)
        tests = Prescription_test.objects.filter(prescription=prescriptions)
        context = {'prescription': prescriptions, 'medicines': medicines, 'tests': tests, 'doctor': doctor}
        return render(request, 'doctor-view-prescription.html', context)

@csrf_exempt
@login_required(login_url="login")
def doctor_view_report(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.filter(user=request.user).first()
        report = Report.objects.get(report_id=pk)
        specimen = Specimen.objects.filter(report=report)
        test = Test.objects.filter(report=report)
        context = {'report': report, 'test': test, 'specimen': specimen, 'doctor': doctor}
        return render(request, 'doctor-view-report.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'doctor-login.html')


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

@csrf_exempt
@login_required(login_url="login")
def doctor_review(request, pk):
    if request.user.is_doctor:
        # doctor = Doctor_Information.objects.filter(user_id=pk).first()        doctor = Doctor_Information.objects.filter(user=request.user).first()
            
        doctor_review = Doctor_review.objects.filter(doctor=doctor)
        
        context = {'doctor': doctor, 'doctor_review': doctor_review}  
        return render(request, 'doctor-profile.html', context)

    if request.user.is_patient:
        doctor = Doctor_Information.objects.get(doctor_id=pk)
        patient = Patient.objects.get(user=request.user)

        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            
            doctor_review = Doctor_review(doctor=doctor, patient=patient, title=title, message=message)
            doctor_review.save()

        context = {'doctor': doctor, 'patient': patient, 'doctor_review': doctor_review}  
        return render(request, 'doctor-profile.html', context)
    else:
        logout(request)


@csrf_exempt
def debug_doctor_list(request):
    """
    Debug view to check what's happening with doctor data
    """
    try:
        # Check if Doctor_Information model exists and has data
        from .models import Doctor_Information
        doctor_count = Doctor_Information.objects.count()
        doctors = Doctor_Information.objects.all()
        
        doctor_list = []
        for doc in doctors:
            doctor_data = {
                'id': getattr(doc, 'doctor_id', getattr(doc, 'id', None)),
                'name': getattr(doc, 'name', 'Unknown'),
                'department_name': getattr(doc, 'department_name', 'General Medicine'),
                'model_fields': [f.name for f in doc._meta.fields]
            }
            doctor_list.append(doctor_data)
        
        return JsonResponse({
            'doctor_count': doctor_count,
            'doctors': doctor_list,
            'model_name': 'Doctor_Information'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)

@require_GET
@login_required
def check_availability(request):
    """
    Simple availability endpoint.
    Returns JSON: { available_times: [ {date: 'YYYY-MM-DD', time: 'HH:MM'} , ... ] }
    """
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'error': 'doctor_id required'}, status=400)

    try:
        doctor = Doctor_Information.objects.get(pk=doctor_id)
    except Doctor_Information.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    # Define candidate time slots per day (adjust to your clinic hours)
    candidate_times = ['09:00', '11:00', '14:00', '16:00']
    available = []

    today = date.today()
    for day_offset in range(0, 7):  # next 7 days
        day = today + timedelta(days=day_offset)
        for t in candidate_times:
            # exclude slots that have a confirmed appointment already
            conflict = Appointment.objects.filter(
                doctor=doctor,
                date=day,
                time=t,
                appointment_status='confirmed'
            ).exists()
            if not conflict:
                available.append({'date': day.isoformat(), 'time': t})

    return JsonResponse({'available_times': available})



