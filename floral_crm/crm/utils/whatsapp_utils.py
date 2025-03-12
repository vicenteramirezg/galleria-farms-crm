from twilio.rest import Client
from django.conf import settings

def send_whatsapp_birthday_message(salesperson, contact):
    """ Sends a WhatsApp reminder to a salesperson about a contact's birthday. """
    
    if not salesperson.phone:
        return "No phone number for salesperson"
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    message_body = (
        f"🎉 Reminder: Today is {contact.name}'s birthday! ({contact.customer.name})\n\n"
        f"Reach out to them via:\n"
        f"📞 Phone: {contact.phone if contact.phone else 'N/A'}\n"
        f"📧 Email: {contact.email if contact.email else 'N/A'}\n\n"
        f"💬 WhatsApp: https://wa.me/{contact.phone if contact.phone else ''}"
    )

    message = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        body=message_body,
        to=f"whatsapp:{salesperson.phone}"
    )
    
    return message.sid
