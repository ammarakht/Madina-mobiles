from django.core.mail import get_connection, EmailMessage, send_mail
from django.conf import settings
from store.models import SiteSettings

def send_custom_email(subject, message, recipient_list, fail_silently=False):
    """
    Sends an email using SiteSettings configured dynamic SMTP details if provided.
    Falls back to settings.py configured EMAIL_BACKEND otherwise.
    """
    try:
        settings_obj = SiteSettings.objects.first()
    except Exception:
        settings_obj = None

    if settings_obj and settings_obj.company_email and settings_obj.email_password:
        # Dynamically create an SMTP connection using Gmail
        from_email = settings_obj.company_email
        try:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host='smtp.gmail.com',
                port=587,
                username=settings_obj.company_email,
                password=settings_obj.email_password,
                use_tls=True,
                fail_silently=fail_silently
            )
            org_name = getattr(settings, 'ORGANIZATION_NAME', 'Madina Mobile Shop')
            email_msg = EmailMessage(
                subject=subject,
                body=message,
                from_email=f"{org_name} <{from_email}>",
                to=recipient_list,
                connection=connection
            )
            email_msg.send(fail_silently=fail_silently)
            return True
        except Exception as e:
            print("Dynamic SMTP Email dispatch failed:", e)
            if not fail_silently:
                raise e

    # Fallback to default EMAIL_BACKEND (e.g. ConsoleBackend during local dev)
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@madinamobileshop.com')
        if settings_obj and settings_obj.company_email:
            org_name = getattr(settings, 'ORGANIZATION_NAME', 'Madina Mobile Shop')
            from_email = f"{org_name} <{settings_obj.company_email}>"
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
        )
        return True
    except Exception as e:
        print("Fallback Email dispatch failed:", e)
        if not fail_silently:
            raise e
        return False
