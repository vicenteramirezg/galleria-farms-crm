import pandas as pd
from django.core.management.base import BaseCommand
from crm.models import Salesperson, Customer, Contact
from django.contrib.auth.models import User
from datetime import date

class Command(BaseCommand):
    help = "Imports CRM data from an Excel file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to the Excel file")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]
        self.stdout.write(self.style.SUCCESS(f"Reading file: {file_path}"))

        # Load the Excel file
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {e}"))
            return
        
        # Iterate over each row and process data
        for index, row in df.iterrows():
            salesperson_name = row["Salesperson Name"]
            salesperson_email = row["salesperson_email"]
            salesperson_phone = row["salesperson_phone"]
            
            customer_name = row["customer"]
            yearly_sales = row["yearly_sales_estimate"]

            contact_first_name = row["first_name"]
            contact_last_name = row["last_name"]
            contact_phone = row["phone"]
            contact_email = row["email"]
            contact_city = row["city"]
            contact_state = row["state"]
            contact_zip = row["zip_code"]
            contact_birthday_month = row["birthday_month"]
            contact_birthday_day = row["birthday_day"]
            contact_relationship_score = row["relationship_score_1_to_5"]
            contact_is_active = row["is_active"]

            # ✅ Create or get Salesperson
            user, created = User.objects.get_or_create(username=salesperson_email, email=salesperson_email)
            salesperson, _ = Salesperson.objects.get_or_create(
                user=user,
                defaults={"phone": salesperson_phone}
            )

            # ✅ Create or get Customer
            customer, _ = Customer.objects.get_or_create(
                name=customer_name,
                defaults={"salesperson": salesperson, "estimated_yearly_sales": yearly_sales}
            )

            # ✅ Create Contact
            if pd.notna(contact_birthday_month) and pd.notna(contact_birthday_day):
                birthday_str = f"{contact_birthday_month} {int(contact_birthday_day)}"
            else:
                birthday_str = None

            Contact.objects.create(
                customer=customer,
                name=f"{contact_first_name} {contact_last_name}",
                phone=contact_phone,
                email=contact_email,
                address=row["address"],
                city=contact_city,
                state=contact_state,
                zip_code=contact_zip,
                birthday=birthday_str,
                relationship_score=contact_relationship_score if pd.notna(contact_relationship_score) else None,
                is_active=bool(contact_is_active)
            )

            self.stdout.write(self.style.SUCCESS(f"Imported {contact_first_name} {contact_last_name} under {customer_name}"))

        self.stdout.write(self.style.SUCCESS("CRM Data Import Completed!"))