from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .pdf import report_pdf


# from . --> same directory
# Views functions and urls must be linked. # of views == # of urls
# App URL file - urls related to hospital

urlpatterns = [
    path('', views.doctor_login, name='doctor-login'),
    path('doctor-login/', views.doctor_login),  # alias to prevent 404 on hard-coded /doctor-login/
    path('doctor-dashboard/',views.doctor_dashboard, name='doctor-dashboard'),
    path('doctor-profile/<int:pk>/', views.doctor_profile, name='doctor-profile'),
    path('doctor-change-password/<int:pk>', views.doctor_change_password,name='doctor-change-password'),
    path('doctor-profile-settings/<int:pk>/', views.doctor_profile_settings,name='doctor-profile-settings'),
    path('doctor-register/', views.doctor_register, name='doctor-register'),
    path('doctor-logout/', views.logoutDoctor, name='doctor-logout'),
    path('my-patients/', views.my_patients, name='my-patients'),
    path('booking/<int:pk>/', views.booking, name='booking'),
    path('booking-success/', views.booking_success, name='booking-success'),
    path('book-appointment/', views.book_appointment, name='book-appointment'),
    path('book-appointment-chatbot/', views.book_appointment_chatbot, name='book-appointment-chatbot'),
    path('get-doctor-list/', views.get_doctor_list, name='get-doctor-list'),
    path('schedule-timings/', views.schedule_timings, name='schedule-timings'),
    path('patient-id/', views.patient_id, name='patient-id'),
    path("patient/search/<int:pk>/", views.patient_search, name="patient-search"),
    path("doctor/logout/", views.doctor_logout, name="doctor-logout"),
    # path("doctor/logout/", views.logout_view, name="doctor-logout"),
    path("doctor/change-password/", views.doctor_change_password, name="doctor-change-password"),
    path("doctor/tests/", views.doctor_test_list, name="doctor-test-list"),
    path('get-doctor-list/', views.get_doctor_list, name='get-doctor-list'),
    path('book-appointment/', views.book_appointment, name='book-appointment'),
    path("patient/<int:pk>/report/", views.download_report_pdf, name="download-report"),
    path('create-prescription/<int:pk>/', views.create_prescription, name='create-prescription'),
    path('patient-profile/<int:pk>/',views.patient_profile, name='patient-profile'),
    path('delete-education/<int:pk>/',views.delete_education, name='delete-education'),
    path('delete-experience/<int:pk>/',views.delete_experience, name='delete-experience'),
    path('appointments/',views.appointments, name='appointments'),
    path('accept-appointment/<int:pk>/',views.accept_appointment, name='accept-appointment'),
    path('reject-appointment/<int:pk>/',views.reject_appointment, name='reject-appointment'),
    path('patient-search/<int:pk>/', views.patient_search, name='patient-search'),
    path('pdf/<int:pk>/',views.report_pdf, name='pdf'),
    path('doctor_review/<int:pk>/', views.doctor_review, name='doctor_review'),
    path('doctor-test-list/', views.doctor_test_list, name='doctor-test-list'),
    path('doctor-view-prescription/<int:pk>/', views.doctor_view_prescription, name='doctor-view-prescription'),
    path('doctor-view-report/<int:pk>/', views.doctor_view_report, name='doctor-view-report'),

]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
