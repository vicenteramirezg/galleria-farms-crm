from django.core.management.base import BaseCommand
from django.utils.timezone import now
from crm.models import Contact  # Ensure this points to the correct path
from crm.utils.email_utils import send_birthday_email  # Import the new function

class Command(BaseCommand):
    help = "Send birthday reminder emails to salespeople"

    def handle(self, *args, **kwargs):
        today = now().date()
        contacts = Contact.objects.filter(birthday_month=today.month, birthday_day=today.day)

        if not contacts.exists():
            self.stdout.write(self.style.SUCCESS("No birthdays today."))
            return

        for contact in contacts:
            salesperson = contact.customer.salesperson  # Fetch the Salesperson
            if not salesperson or not salesperson.user or not salesperson.user.email:
                continue  # Skip if salesperson has no associated user or email

            send_birthday_email(salesperson, contact)  # 🎯 Call the function

            self.stdout.write(self.style.SUCCESS(f"Email sent to {salesperson.user.email} for {contact.name}"))
