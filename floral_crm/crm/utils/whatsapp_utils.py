from twilio.rest import Client
from django.conf import settings
import json  # ✅ Import JSON to ensure correct formatting

def send_whatsapp_birthday_message(salesperson, contact):
    """ Sends a WhatsApp reminder to a salesperson about a contact's birthday using Twilio template. """
    
    if not salesperson.phone:
        return "No phone number for salesperson"
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Define the template parameters (must match the template placeholders)
    message_params = {
        "1": salesperson.user.first_name,  # {{1}} Salesperson name
        "2": contact.name,  # {{2}} Contact name
        "3": contact.customer.name,  # {{3}} Contact Customer
        "4": contact.phone if contact.phone else "N/A",  # {{4}} Phone
        "5": contact.email if contact.email else "N/A",  # {{5}} Email
        "6": f"https://wa.me/{contact.phone}" if contact.phone else "N/A"  # {{6}} WhatsApp link
    }

    # ✅ Convert message_params to a proper JSON string
    content_variables_json = json.dumps(message_params)

    # Send WhatsApp message using Twilio Template Message
    message = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{salesperson.phone}",
        content_sid="HXfaab57dc9c6885a088e809fddda5f790",  # Replace with your actual Template SID
        content_variables=content_variables_json  # ✅ Ensure correct JSON format
    )
    
    return message.sid