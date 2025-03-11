from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from crm.models import Salesperson  # ✅ Import the correct model
from email.utils import formataddr  # ✅ Import for correct email formatting


class Command(BaseCommand):
    help = "Send a welcome email with password reset link to a specific salesperson"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="The email of the salesperson to send the welcome email to")

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        try:
            salesperson = Salesperson.objects.select_related("user").get(user__email=email)
            user = salesperson.user  # ✅ Get the associated User

            # Generate password reset token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"https://{settings.ALLOWED_HOSTS[0]}/reset/{uid}/{token}/"

            # ✅ Properly formatted sender email
            from_email = formataddr(("Galleria Farms Data Command CRM", settings.DEFAULT_FROM_EMAIL))  # ✅ Correctly formats the sender

            # Render email content
            subject = "🚀 Welcome to Galleria Farms CRM - Set Your Password"
            html_message = render_to_string("registration/welcome_email.html", {
                "user": user,
                "reset_link": reset_link,
            })
            plain_message = f"""
Hello {user.get_full_name()},

Welcome to Galleria Farms CRM! 🎉

Your username: {user.username}

To secure your account, please reset your password using the following link:
{reset_link}

If you did not request this, please ignore this email.

Best,  
Galleria Farms CRM Team
            """

            # Send email
            send_mail(
                subject,
                plain_message,
                from_email,  # ✅ Fixed sender
                [user.email],
                fail_silently=False,
                html_message=html_message,
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Welcome email sent to {user.email}"))

        except Salesperson.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No salesperson found with email: {email}"))
