from twilio.rest import Client
from django.conf import settings

def send_whatsapp_birthday_message(salesperson, contact):
    """ Sends a WhatsApp reminder to a salesperson about a contact's birthday. """
    
    if not salesperson.phone:
        return "No phone number for salesperson"
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Define the template parameters (must match the template placeholders)
    message_params = [
        salesperson.user.first_name,  # {{1}} Salesperson name
        contact.name,  # {{2}} Contact name
        contact.customer.name,  # {{3}} Contact Customer
        contact.phone if contact.phone else "N/A",  # {{4}} Phone
        contact.email if contact.email else "N/A",  # {{5}} Email
        f"https://wa.me/{contact.phone}" if contact.phone else "N/A"  # {{6}} WhatsApp link
    ]

    message = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{salesperson.phone}",
        content_sid="HXfaab57dc9c6885a088e809fddda5f790",  # Replace with actual Template SID
        content_variables={"1": message_params[0], "2": message_params[1], "3": message_params[2], "4": message_params[3], "5": message_params[4], "6": message_params[5]}
    )
    
    return message.sid
