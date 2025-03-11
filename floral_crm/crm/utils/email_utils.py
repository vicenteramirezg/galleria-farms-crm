from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def send_birthday_email(salesperson, contact):
    """ Sends a beautiful HTML email reminder to the salesperson when a contact has a birthday. """
    subject = f"🎉 Reminder: {contact.name}'s Birthday Today!"
    
    # Set sender email with custom display name
    from_email = "Galleria Farms Data Command CRM <donotreply@galleriafarms.com>"

    # Generate WhatsApp and Email Links
    whatsapp_link = f"https://wa.me/{contact.phone}" if contact.phone else "#"
    email_link = f"mailto:{contact.email}" if contact.email else "#"
    
    # HTML Email Content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎉 Birthday Reminder</title>
        <style>
            body {{ font-family: 'Poppins', sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .email-container {{ max-width: 600px; background: #ffffff; margin: 20px auto; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }}
            .header {{ background-color: #211f20; padding: 20px; text-align: center; }}
            .header img {{ height: 50px; }}
            .content {{ padding: 30px; color: #333; text-align: center; }}
            .content h2 {{ color: #211f20; font-size: 22px; margin-bottom: 10px; }}
            .content p {{ font-size: 16px; line-height: 1.6; }}
            .button-container {{ margin-top: 20px; text-align: center; }}
            .cta-button, .whatsapp-button, .email-button {{
                display: inline-block;
                text-decoration: none;
                padding: 12px 20px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: 600;
                margin: 5px;
            }}
            .cta-button {{ background-color: #007bff; color: #ffffff; }}
            .cta-button:hover {{ background-color: #0056b3; }}
            .whatsapp-button {{ background-color: #25D366; color: #ffffff; }}
            .whatsapp-button:hover {{ background-color: #1DA851; }}
            .email-button {{ background-color: #17A2B8; color: #ffffff; }}
            .email-button:hover {{ background-color: #138496; }}
            .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 14px; color: #666; }}
            .footer a {{ color: #007bff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <img src="https://crm.galleriafarms.com/static/img/logo_white.png" alt="Galleria Farms CRM">
            </div>
            <div class="content">
                <h2>🎉 Don't forget to reach out!</h2>
                <p>Hello <strong>{salesperson.user.first_name}</strong>,</p>
                <p>Today is <strong>{contact.name} ({contact.customer.name})</strong>'s birthday! 🎂</p>
                <p>Take a moment to send them a quick message or give them a call.</p>

                <div class="button-container">
                    <a href="https://crm.galleriafarms.com/crm/dashboard/" class="cta-button">Go to Dashboard</a>
                    {f'<a href="{whatsapp_link}" class="whatsapp-button">💬 Send a message</a>' if contact.phone else ''}
                    {f'<a href="{email_link}" class="email-button">📧 Send an email</a>' if contact.email else ''}
                </div>
            </div>

            <div class="footer">
                <p>Galleria Farms Data Command - CRM</p>
                <p><a href="https://crm.galleriafarms.com">Visit Dashboard</a> | <a href="mailto:vramirez@galleriafarms.com">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    # Plain text version (fallback)
    text_content = strip_tags(html_content)

    # Create the email with a custom sender name
    email = EmailMultiAlternatives(
        subject,
        text_content,
        from_email,  # 🎯 Custom sender name here!
        [salesperson.user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
