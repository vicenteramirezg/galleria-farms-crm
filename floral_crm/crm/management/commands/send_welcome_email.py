from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

class Command(BaseCommand):
    help = "Send a welcome email with password reset link to a specific user"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="The email of the user to send the welcome email to")

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        try:
            user = User.objects.get(email=email)

            # Generate password reset token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"https://{settings.ALLOWED_HOSTS[0]}/reset/{uid}/{token}/"  # ✅ Force HTTPS

            # ✅ Get sender email dynamically from environment variables
            sender_email = settings.DEFAULT_FROM_EMAIL

            # Render email content
            subject = "🌟 Welcome to Galleria Farms CRM - Set Your Password"
            html_message = render_to_string("registration/welcome_email.html", {
                "user": user,
                "reset_link": reset_link
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

            # ✅ Send email (HTML & Plain Text)
            send_mail(
                subject,
                plain_message,
                sender_email,  # ✅ Uses environment variable DEFAULT_FROM_EMAIL
                [user.email],
                fail_silently=False,
                html_message=html_message,  # Sends both plain & HTML versions
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Welcome email sent to {user.email} from {sender_email}"))  # ✅ Keep for CLI usage

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No user found with email: {email}"))  # ✅ Handle missing user gracefully
