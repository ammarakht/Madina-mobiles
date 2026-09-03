from django.core.mail import get_connection, EmailMessage, send_mail
from django.conf import settings
from store.models import SiteSettings

def send_custom_email(subject, message, recipient_list, html_message=None, fail_silently=False):
    """
    Sends an email using SiteSettings configured dynamic SMTP details if provided.
    Falls back to settings.py configured EMAIL_BACKEND otherwise.
    Supports both plain text message and rich HTML email.
    """
    try:
        settings_obj = SiteSettings.objects.first()
    except Exception:
        settings_obj = None

    from_email_addr = (settings_obj.company_email if (settings_obj and settings_obj.company_email) 
                       else getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@madinamobileshop.com'))
    org_name = getattr(settings, 'ORGANIZATION_NAME', 'Madina Mobile Shop')
    formatted_from = f"{org_name} <{from_email_addr}>"

    if settings_obj and settings_obj.company_email and settings_obj.email_password:
        # Dynamically create an SMTP connection using Gmail
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
            email_msg = EmailMessage(
                subject=subject,
                body=html_message if html_message else message,
                from_email=formatted_from,
                to=recipient_list,
                connection=connection
            )
            if html_message:
                email_msg.content_subtype = "html"
            email_msg.send(fail_silently=fail_silently)
            return True
        except Exception as e:
            print("Dynamic SMTP Email dispatch failed:", e)
            if not fail_silently:
                raise e

    # Fallback to default EMAIL_BACKEND (e.g. ConsoleBackend during local dev)
    try:
        if html_message:
            from django.core.mail import EmailMultiAlternatives
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=formatted_from,
                to=recipient_list
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=fail_silently)
        else:
            send_mail(
                subject=subject,
                message=message,
                from_email=formatted_from,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
            )
        return True
    except Exception as e:
        print("Fallback Email dispatch failed:", e)
        if not fail_silently:
            raise e
        return False
