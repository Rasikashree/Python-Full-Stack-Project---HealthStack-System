from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
# from django.contrib.auth.models import User

from .models import Doctor_Information
from hospital.models import User, Hospital_Information


# # from django.core.mail import send_mail
# # from django.conf import settings


@receiver(post_save, sender=Doctor_Information)
def updateUser(sender, instance, created, **kwargs):
    # user.profile or below (1-1 relationship goes both ways)
    doctor = instance
    user = doctor.user

    if created is False:
        user.first_name = "Dr."  # prefix/title
        user.last_name = doctor.name if doctor.name else "Unknown"
        user.username = doctor.username if doctor.username else user.username
        user.email = doctor.email if doctor.email else user.email
        user.save()


@receiver(post_save, sender=User)
def ensure_doctor_hospital_registration(sender, instance, created, **kwargs):
    """
    Whenever a `User` with `is_doctor=True` is saved, ensure there is at least
    one `Doctor_Information` row for that user associated with a hospital.
    This guarantees that creating a doctor login also creates the hospital register.
    """
    user = instance
    try:
        if user.is_doctor and not Doctor_Information.objects.filter(user=user).exists():
            default_hospital = Hospital_Information.objects.first()
            if default_hospital is None:
                default_hospital = Hospital_Information.objects.create(name='Default Hospital')
            Doctor_Information.objects.create(
                user=user,
                username=user.username,
                email=user.email,
                hospital_name=default_hospital,
            )
    except Exception:
        # Avoid breaking user saves due to signal errors
        pass

