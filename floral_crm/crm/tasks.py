from celery import shared_task
from django.utils.timezone import now
from crm.utils.email_utils import send_birthday_email
from crm.utils.whatsapp_utils import send_whatsapp_birthday_message

MANAGER_PHONE = "+13055190251"

# ✅ Lazy model import to prevent "Apps aren't loaded yet" error
def get_contact_model():
    from django.apps import apps
    return apps.get_model("crm", "Contact")

@shared_task(name="crm.tasks.send_birthday_reminders")
def send_birthday_reminders():
    """ Celery task to send birthday reminders to salespeople """
    Contact = get_contact_model()  # ✅ Load model dynamically
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
    """ Celery task to send WhatsApp birthday reminders to salespeople """
    Contact = get_contact_model()  # ✅ Load model dynamically
    today = now().date()
    contacts = Contact.objects.filter(birthday_month=today.month, birthday_day=today.day)

    if not contacts.exists():
        return "No birthdays today."

    for contact in contacts:
        salesperson = contact.customer.salesperson

        # ✅ Send message to salesperson (if they have a phone number)
        if salesperson and salesperson.phone:
            send_whatsapp_birthday_message(salesperson, contact)

        # ✅ Send message to the manager (always)
        send_whatsapp_birthday_message(
            type("Manager", (object,), {"phone": MANAGER_PHONE, "user": type("User", (object,), {"first_name": "Manager"})}),
            contact
        )

    return f"WhatsApp birthday reminders sent for {contacts.count()} contacts (Salespeople & Manager)."
