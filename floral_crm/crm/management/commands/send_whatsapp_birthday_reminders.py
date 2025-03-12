from django.core.management.base import BaseCommand
from django.utils.timezone import now
from crm.models import Contact  # Adjust the import if necessary
from crm.utils.whatsapp_utils import send_whatsapp_birthday_message

class Command(BaseCommand):
    help = "Send birthday reminder WhatsApp messages to salespeople"

    def handle(self, *args, **kwargs):
        today = now().date()
        contacts = Contact.objects.filter(birthday_month=today.month, birthday_day=today.day)

        if not contacts.exists():
            self.stdout.write(self.style.SUCCESS("No birthdays today."))
            return

        for contact in contacts:
            salesperson = contact.customer.salesperson  # Fetch the Salesperson
            
            if not salesperson or not salesperson.phone:
                continue  # Skip if no salesperson or no phone number

            # Send WhatsApp reminder
            message_sid = send_whatsapp_birthday_message(salesperson, contact)
            
            self.stdout.write(self.style.SUCCESS(
                f"WhatsApp message sent to {salesperson.phone} for {contact.name} (SID: {message_sid})"
            ))
