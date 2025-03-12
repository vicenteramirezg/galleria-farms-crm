from celery import shared_task
from django.utils.timezone import now
from crm.models import Contact
from crm.utils.email_utils import send_birthday_email
from crm.utils.whatsapp_utils import send_whatsapp_birthday_message

MANAGER_PHONE = "+13055190251"

@shared_task(name="crm.tasks.send_birthday_reminders")
def send_birthday_reminders():
    today = now().date()
    contacts = Contact.objects.filter(birthday_month=today.month, birthday_day=today.day)
    if not contacts.exists():
        return "No birthdays today."
    for contact in contacts:
        salesperson = contact.customer.salesperson
        if salesperson and salesperson.user and salesperson.user.email:
            send_birthday_email(salesperson, contact)
    return f"Sent {contacts.count()} birthday reminder emails"

@shared_task(name="crm.tasks.send_whatsapp_birthday_reminders")
def send_whatsapp_birthday_reminders():
    today = now().date()
    contacts = Contact.objects.filter(birthday_month=today.month, birthday_day=today.day)
    if not contacts.exists():
        return "No birthdays today."
    for contact in contacts:
        salesperson = contact.customer.salesperson
        if salesperson and salesperson.phone:
            send_whatsapp_birthday_message(salesperson, contact)
        send_whatsapp_birthday_message(
            type("Manager", (object,), {"phone": MANAGER_PHONE, "user": type("User", (object,), {"first_name": "Manager"})}),
            contact
        )
    return f"WhatsApp birthday reminders sent for {contacts.count()} contacts (Salespeople & Manager)."