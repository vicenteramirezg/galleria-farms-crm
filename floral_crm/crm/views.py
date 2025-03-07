# Django core imports
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView, DetailView
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.contrib import messages

# Django database and utility imports
from django.db.models import Sum, Avg, Count, Q
from django.db.models.functions import ExtractMonth, ExtractDay

# Models and forms
from .models import Customer, Contact, Salesperson, Profile, Role
from .forms import CustomerForm, ContactForm, SignupForm  # Ensure you have this form

# Python standard library imports
import csv
from collections import defaultdict
import logging
from datetime import timedelta, date

logger = logging.getLogger(__name__)  # Setup logging for debugging

# Dictionary to map month numbers to names
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

def home(request):
    return render(request, 'home.html')

def custom_404_view(request, exception):
    """ Custom 404 Page """
    return render(request, "404.html", status=404)

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            print(form.errors)  # Debugging: Print errors to console

    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})

class CustomLogoutView(View):
    @method_decorator(csrf_exempt)  # Disable CSRF for GET requests only (Django handles CSRF in forms)
    def post(self, request):
        logout(request)
        return redirect('/')

    def get(self, request):
        # Prevent direct GET requests to the logout URL
        return HttpResponseNotAllowed(["POST"])

class SalespersonAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.salesperson.customers.filter(id=kwargs.get('pk')).exists():
            raise PermissionDenied("You do not have access to this customer.")
        return super().dispatch(request, *args, **kwargs)

from datetime import date, timedelta
from django.db.models import Q

# Dictionary to map month numbers to names
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

@login_required
def dashboard(request):
    """ Generates summary metrics based on the user's role:
        - Executives see all customers & contacts.
        - Managers see only customers & contacts within their department.
        - Salespeople see only their assigned customers & contacts.
    """
    user = request.user
    salesperson = getattr(user, 'salesperson', None)

    # Role-based filtering logic
    if user.profile.role == Role.EXECUTIVE:
        customers = Customer.objects.prefetch_related("contacts")  # ✅ Executives see everything

    elif "Manager" in user.profile.role:
        department_name = user.profile.role.replace("Manager - ", "").lower()
        customers = Customer.objects.filter(department=department_name).prefetch_related("contacts")  # ✅ Managers see their department's data

    else:  # Salesperson role
        customers = Customer.objects.filter(salesperson=salesperson).prefetch_related("contacts")  # ✅ Salespeople see only their assigned customers

    # Calculate key statistics
    total_sales = customers.aggregate(Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
    total_contacts = Contact.objects.filter(customer__in=customers).count()
    avg_relationship_score = Contact.objects.filter(customer__in=customers).aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0

    # Prepare data for top customers
    top_customers = customers.order_by("-estimated_yearly_sales")[:5]  # Top 5 by sales

    # Enrich customer data with aggregated contact stats
    customer_data = []
    for customer in customers:
        num_contacts = customer.contacts.count()
        avg_score = customer.contacts.aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0
        customer_data.append({
            "id": customer.id,
            "name": customer.name,
            "sales": customer.estimated_yearly_sales,
            "num_contacts": num_contacts,
            "avg_score": round(avg_score, 2) if avg_score else "N/A"
        })

    # ✅ Fix upcoming birthdays filtering logic
    today = date.today()
    today_month, today_day = today.month, today.day
    future_date = today + timedelta(days=30)
    future_month, future_day = future_date.month, future_date.day

    upcoming_birthdays = Contact.objects.filter(
        customer__in=customers
    ).filter(
        Q(birthday_month=today_month, birthday_day__gte=today_day) |  # Birthdays later this month
        Q(birthday_month=future_month, birthday_day__lte=future_day) |  # Birthdays early next month
        Q(birthday_month__gt=today_month, birthday_month__lt=future_month)  # Birthdays in-between
    ).order_by("birthday_month", "birthday_day")

    # ✅ Ensure clean birthday formatting
    for contact in upcoming_birthdays:
        try:
            month_int = int(contact.birthday_month)  # Convert to int if stored as string
            month_name = MONTH_NAMES.get(month_int)  # Get month name from dictionary
        except (ValueError, TypeError):
            month_name = None  # Handle invalid values safely

        if month_name:  # ✅ Ensure it's valid
            contact.clean_birthday = f"{month_name}, {contact.birthday_day}"
        else:
            contact.clean_birthday = "Not provided"  # Handle missing or incorrect data

    return render(request, "crm/dashboard.html", {
        "customers": customer_data,
        "total_sales": f"${total_sales:,.0f}",  # Format with commas
        "total_contacts": total_contacts,
        "avg_relationship_score": round(avg_relationship_score, 2) if avg_relationship_score else "N/A",
        "top_customers": top_customers,
        "upcoming_birthdays": upcoming_birthdays
    })

class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "crm/customer_form.html"
    success_url = reverse_lazy("crm:customer_list")

    def test_func(self):
        """ 
        Ensure the correct access:
        - Executives can edit all customers.
        - Salespersons can only edit their own customers.
        - Managers can edit customers only under their assigned department.
        """
        user = self.request.user
        customer = self.get_object()

        if user.profile.role == "Executive":
            return True  # ✅ Executives can edit any customer
        elif "Manager" in user.profile.role:
            # ✅ Convert Manager role to department
            role_to_department = {
                "Manager - Mass Market": Customer.MASS_MARKET,
                "Manager - MM2": Customer.MM2,
                "Manager - Ecommerce": Customer.ECOMMERCE,
                "Manager - Wholesale": Customer.WHOLESALE,
            }
            department = role_to_department.get(user.profile.role, None)

            # ✅ Allow Managers to edit customers only in their department
            if department and customer.department == department:
                return True
        elif user.profile.role == "Salesperson":
            return customer.salesperson == user.salesperson  # ✅ Salespersons can only edit their own customers

        return False  # 🚫 Block unauthorized users

    def get_queryset(self):
        """ Ensure the user can only retrieve customers they are allowed to edit. """
        user = self.request.user

        if user.profile.role == "Executive":
            queryset = Customer.objects.all()  # ✅ Executives see all customers
        elif "Manager" in user.profile.role:
            # Convert role to correct department key
            role_to_department = {
                "Manager - Mass Market": Customer.MASS_MARKET,
                "Manager - MM2": Customer.MM2,
                "Manager - Ecommerce": Customer.ECOMMERCE,
                "Manager - Wholesale": Customer.WHOLESALE,
            }
            department = role_to_department.get(user.profile.role, None)
            if department:
                queryset = Customer.objects.filter(department=department)  # ✅ Managers see only their department's customers
            else:
                queryset = Customer.objects.none()  # 🚫 If no valid department, deny access
        else:
            queryset = Customer.objects.filter(salesperson=user.salesperson)  # ✅ Salespersons see only their own customers

        # 🛑 Debugging
        print(f"🔍 User: {user}, Role: {user.profile.role}, Allowed Customers: {queryset}")

        return queryset

    def get_form_kwargs(self):
        """ Pass the logged-in user to the form to ensure proper salesperson handling. """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ✅ Pass user to form
        return kwargs

    def form_valid(self, form):
        """ 
        - Ensure Salesperson remains unchanged if edited by a Salesperson.
        - Allow Executives and Managers to modify the assigned Salesperson.
        """
        user = self.request.user

        # ✅ Prevent Salespersons from changing the assigned Salesperson
        if user.profile.role == "Salesperson":
            form.instance.salesperson = self.object.salesperson  # ✅ Keep original salesperson

        logger.info(f"🔹 Form Data Before Saving: {form.cleaned_data}")

        response = super().form_valid(form)

        # 🔥 Fetch updated customer from the database to verify changes
        updated_customer = get_object_or_404(Customer, id=form.instance.id)
        logger.info(f"✅ Updated Customer: {updated_customer.name}, Sales: {updated_customer.estimated_yearly_sales}")

        messages.success(self.request, "Customer details updated successfully!")  # ✅ Show success message

        return response

    def form_invalid(self, form):
        """ Log invalid form submissions for debugging and show an error message """
        logger.error(f"❌ CustomerEditView - FORM INVALID: {form.errors}")
        messages.error(self.request, "There were errors in your form submission. Please correct them.")
        return super().form_invalid(form)


class ContactUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"
    success_url = reverse_lazy("crm:contact_list")

    def test_func(self):
        """ 
        Ensure the correct access:
        - Executives can edit all contacts.
        - Managers can edit contacts within their department.
        - Salespersons can only edit their own customers' contacts.
        """
        user = self.request.user
        contact = self.get_object()

        if user.profile.role == "Executive":
            return True  # ✅ Executives can edit any contact
        elif "Manager" in user.profile.role:
            # ✅ Convert Manager role to department
            role_to_department = {
                "Manager - Mass Market": Customer.MASS_MARKET,
                "Manager - MM2": Customer.MM2,
                "Manager - Ecommerce": Customer.ECOMMERCE,
                "Manager - Wholesale": Customer.WHOLESALE,
            }
            department = role_to_department.get(user.profile.role, None)

            # ✅ Allow Managers to edit contacts only within their department
            if department and contact.customer.department == department:
                return True
        elif user.profile.role == "Salesperson":
            return contact.customer.salesperson == user.salesperson  # ✅ Salespersons edit only their own customers' contacts

        return False  # 🚫 Block unauthorized users

    def get_queryset(self):
        """ Ensure the user can only retrieve contacts they are allowed to edit. """
        user = self.request.user

        if user.profile.role == "Executive":
            queryset = Contact.objects.all()  # ✅ Executives see all contacts
        elif "Manager" in user.profile.role:
            # Convert role to correct department key
            role_to_department = {
                "Manager - Mass Market": Customer.MASS_MARKET,
                "Manager - MM2": Customer.MM2,
                "Manager - Ecommerce": Customer.ECOMMERCE,
                "Manager - Wholesale": Customer.WHOLESALE,
            }
            department = role_to_department.get(user.profile.role, None)
            if department:
                queryset = Contact.objects.filter(customer__department=department)  # ✅ Managers see only their department's contacts
            else:
                queryset = Contact.objects.none()  # 🚫 If no valid department, deny access
        else:
            queryset = Contact.objects.filter(customer__salesperson=user.salesperson)  # ✅ Salespersons see only their own customers' contacts

        # 🛑 Debugging
        print(f"🔍 User: {user}, Role: {user.profile.role}, Allowed Contacts: {queryset}")

        return queryset

    def form_valid(self, form):
        """ Ensure the customer remains unchanged when saving the contact """
        contact = form.save(commit=False)
        contact.customer = self.get_object().customer  # ✅ Keep the original customer
        contact.address = form.cleaned_data["address"]  # ✅ Explicitly save address
        contact.save()
        messages.success(self.request, "Contact details updated successfully!")  # ✅ Show success message
        return super().form_valid(form)

    def form_invalid(self, form):
        """ Log errors if the form is invalid """
        messages.error(self.request, "There were errors updating the contact.")
        logger.error(f"FORM INVALID ERRORS: {form.errors}")  # Debugging
        return super().form_invalid(form)

@login_required
def export_contacts(request):
    """ Exports contacts into a CSV file with additional fields: Birthday (Month & Day) & Salesperson """

    # Get contacts associated with the logged-in salesperson
    contacts = Contact.objects.filter(customer__salesperson=request.user.salesperson)

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    # Set up the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Customer', 'Relationship Score', 'Birthday Month', 'Birthday Day', 'Salesperson'])

    # Write contact data to CSV
    for contact in contacts:
        writer.writerow([
            contact.name,
            contact.phone if contact.phone else "N/A",
            contact.email if contact.email else "N/A",
            contact.customer.name if contact.customer else "N/A",  # Handle missing customer
            contact.relationship_score,
            contact.get_birthday_month_display() if contact.birthday_month else "Not provided",  # Fetch month name
            contact.birthday_day if contact.birthday_day else "Not provided",  # Fetch day
            contact.customer.salesperson.user.get_full_name() if contact.customer and contact.customer.salesperson else "N/A"  # Fetch salesperson's name
        ])

    return response

@login_required
def export_customers(request):
    """ Exports customers into a CSV file with key details """

    # Get customers associated with the logged-in salesperson
    customers = Customer.objects.filter(salesperson=request.user.salesperson)

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'

    # Set up the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Department', 'Estimated Yearly Sales', 'Salesperson'])

    # Write customer data to CSV
    for customer in customers:
        writer.writerow([
            customer.name,
            customer.get_department_display(),  # Use display name for department
            f"${customer.estimated_yearly_sales:,.0f}",  # Format sales with commas and no decimals
            customer.salesperson.user.get_full_name() if customer.salesperson else "N/A"  # Fetch salesperson's name
        ])

    return response

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/add_customer.html'
    success_url = reverse_lazy('crm:customer_list')

    def get_form_kwargs(self):
        """ Pass the logged-in user to the form for role-based logic """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass user to form
        return kwargs

    def form_valid(self, form):
        """ Ensure correct salesperson is assigned based on user role """

        if self.request.user.profile.role == "Executive":
            # Allow Executives to assign a salesperson
            form.instance.salesperson = form.cleaned_data.get("salesperson")
        else:
            # Salespeople can only assign themselves
            form.instance.salesperson = self.request.user.salesperson

        # 🔹 Log cleaned form data
        logger.info(f"🔹 Form Data Before Saving: {form.cleaned_data}")

        response = super().form_valid(form)

        # 🔥 Fetch newly created customer from the database
        new_customer = get_object_or_404(Customer, id=form.instance.id)
        logger.info(f"✅ New Customer Created: {new_customer.name}, Sales: {new_customer.estimated_yearly_sales}, Salesperson: {new_customer.salesperson}")

        return response

@login_required
def add_customer(request):
    """ Handles customer creation with role-based salesperson assignment """
    
    if request.method == "POST":
        form = CustomerForm(request.POST, user=request.user)
        
        if form.is_valid():
            customer = form.save(commit=False)

            if request.user.profile.role == "Executive":
                # Executives can select a salesperson
                customer.salesperson = form.cleaned_data.get("salesperson")
            else:
                # Salespeople automatically assigned
                customer.salesperson = request.user.salesperson

            customer.save()
            return redirect("crm:customer_list")
        else:
            logger.error(f"❌ Customer Form Errors: {form.errors}")  # Debugging

    else:
        form = CustomerForm(user=request.user)  # Pass user to form

    return render(request, "crm/add_customer.html", {"form": form})

@login_required
def customer_list(request):
    """ Fetch customers based on user role:
        - Executives see all customers.
        - Salespersons see only their assigned customers.
        - Managers see only customers within their department.
    """

    user = request.user

    if user.profile.role == Role.EXECUTIVE:
        customers = Customer.objects.all()  # ✅ Executives see all customers
    elif user.profile.role == Role.SALESPERSON:
        customers = Customer.objects.filter(salesperson=user.salesperson)  # ✅ Salespersons see only their own
    else:
        # ✅ Managers see only customers in their assigned department
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
        }
        department = department_mapping.get(user.profile.role)

        if department:
            customers = Customer.objects.filter(department=department)
        else:
            customers = Customer.objects.none()  # 🚫 No access if no valid department

    # ✅ Group customers by department & order alphabetically
    grouped_customers = defaultdict(list)
    for customer in customers.order_by("department", "name"):
        grouped_customers[customer.department].append(customer)

    return render(request, "crm/customer_list.html", {"grouped_customers": dict(grouped_customers)})

@login_required
def contact_list(request):
    """ Groups contacts by department → customer → ordered contacts based on user roles. """

    user = request.user

    # ✅ Executives see all contacts
    if user.profile.role == Role.EXECUTIVE:
        customers = Customer.objects.prefetch_related("contacts").order_by("department", "name")

    # ✅ Salespersons see only their assigned customers' contacts
    elif user.profile.role == Role.SALESPERSON:
        customers = Customer.objects.filter(salesperson=user.salesperson) \
                                    .prefetch_related("contacts") \
                                    .order_by("department", "name")

    # ✅ Managers see only customers within their assigned department
    else:
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
        }
        department = department_mapping.get(user.profile.role)

        if department:
            customers = Customer.objects.filter(department=department).prefetch_related("contacts").order_by("department", "name")
        else:
            customers = Customer.objects.none()  # 🚫 No access if no valid department

    grouped_contacts = defaultdict(list)

    # ✅ Organize customers under their respective departments
    for customer in customers:
        sorted_contacts = sorted(customer.contacts.all(), key=lambda contact: contact.name.lower())  # Alphabetical sorting

        for contact in sorted_contacts:
            # ✅ Format birthday properly
            birthday_month = int(contact.birthday_month) if contact.birthday_month else None
            birthday_day = contact.birthday_day

            clean_birthday = f"{MONTH_NAMES.get(birthday_month, 'Unknown')}, {birthday_day}" if birthday_month and birthday_day else "Not provided"
            contact.clean_birthday = clean_birthday  # Attach formatted birthday

        customer.sorted_contacts = sorted_contacts  # Store sorted contacts
        grouped_contacts[customer.department].append(customer)  # Group by department

    return render(request, "crm/contact_list.html", {"grouped_contacts": dict(grouped_contacts)})

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "crm/contact_list.html"  # Your template for displaying contacts
    context_object_name = "contacts"  # Name used for the context in the template

    def get_queryset(self):
        """ Fetch contacts based on user role:
            - Executives see all contacts.
            - Salespersons see only contacts from their assigned customers.
            - Managers see only contacts from customers in their department.
        """
        user = self.request.user

        if user.profile.role == Role.EXECUTIVE:
            return Contact.objects.all().order_by("name")  # ✅ Executives see all contacts

        if user.profile.role == Role.SALESPERSON:
            return Contact.objects.filter(customer__salesperson=user.salesperson).order_by("name")  # ✅ Salespersons filter

        # ✅ Managers see only contacts within their department
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
        }
        department = department_mapping.get(user.profile.role)

        if department:
            return Contact.objects.filter(customer__department=department).order_by("name")  # ✅ Managers see their department's contacts

        return Contact.objects.none()  # 🚫 No access if no valid department

@login_required
def add_contact(request):
    """ Allows adding a new contact with optional pre-filled customer selection. """
    customer_id = request.GET.get("customer_id")  # ✅ Get customer ID from URL
    customer = None

    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)  # ✅ Ensure customer exists

    if request.method == "POST":
        form = ContactForm(request.POST, user=request.user)  # ✅ Pass user context
        if form.is_valid():
            contact = form.save(commit=False)
            contact.phone = form.cleaned_data['phone']  # ✅ Ensure correct phone formatting

            # 🚀 **Ensure the customer is assigned properly**
            if customer:
                contact.customer = customer
            elif "customer" in form.cleaned_data and form.cleaned_data["customer"]:
                contact.customer = form.cleaned_data["customer"]
            else:
                form.add_error("customer", "This field is required.")
                return render(request, "crm/add_contact.html", {"form": form, "customer": customer})

            contact.save()
            logger.info(f"✅ Contact Created: {contact.name} - Redirecting to customer {contact.customer.id}")

            # 🚀 **Fixed redirect**
            return HttpResponseRedirect(reverse("crm:customer_detail", args=[contact.customer.id]))  # ✅ Correct way to redirect
    else:
        form = ContactForm(user=request.user, initial={"customer": customer} if customer else {})

    return render(request, "crm/add_contact.html", {"form": form, "customer": customer})

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = "crm/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        """Add additional customer-related data."""
        context = super().get_context_data(**kwargs)
        customer = self.get_object()

        # Get all contacts related to the customer
        contacts = customer.contacts.all()

        # Calculate clean_birthday for each contact
        for contact in contacts:
            # Ensure birthday_month is an integer
            birthday_month = int(contact.birthday_month) if contact.birthday_month else None
            birthday_day = contact.birthday_day

            # Generate a clean birthday format
            if birthday_month and birthday_day:
                clean_birthday = f"{MONTH_NAMES.get(birthday_month, 'Unknown')}, {birthday_day}"
            else:
                clean_birthday = "Not provided"

            # Attach clean_birthday to the contact
            contact.clean_birthday = clean_birthday

        # Calculate average relationship score
        avg_relationship_score = contacts.aggregate(avg_score=Avg("relationship_score"))["avg_score"]

        context.update({
            "contacts": contacts,
            "avg_relationship_score": avg_relationship_score if avg_relationship_score else "No scores yet",
        })
        return context

def executive_required(view_func):
    """ Custom decorator to restrict access to Executives only. """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, "profile") or request.user.profile.role != "Executive":
            return render(request, "crm/403.html", status=403)  # Show 403 page if unauthorized
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@executive_required  # ✅ Ensures only Executives can access this page
def executive_dashboard(request):
    """ View for Executives to see an overview of all users and their performance. """

    # Retrieve all users with their role, sorted alphabetically by full name
    users = Profile.objects.select_related("user").order_by("user__first_name", "user__last_name")

    # Build a list with additional stats
    user_data = []
    for profile in users:
        salesperson = getattr(profile.user, "salesperson", None)

        if salesperson:
            total_customers = Customer.objects.filter(salesperson=salesperson).count()
            total_contacts = Contact.objects.filter(customer__salesperson=salesperson).count()
            total_sales = Customer.objects.filter(salesperson=salesperson).aggregate(Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
            avg_relationship_score = Contact.objects.filter(customer__salesperson=salesperson).aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0
        else:
            total_customers = total_contacts = total_sales = avg_relationship_score = "N/A"  # Executives may not have sales data

        user_data.append({
            "username": profile.user.username,
            "full_name": profile.user.get_full_name(),
            "role": profile.role,
            "total_customers": total_customers,
            "total_contacts": total_contacts,
            "total_sales": total_sales,
            "avg_relationship_score": round(avg_relationship_score, 2) if avg_relationship_score != "N/A" else "N/A"
        })

    return render(request, "crm/executive_dashboard.html", {"user_data": user_data})

@login_required
def manager_dashboard(request):
    """ View for Managers to see an overview of salespeople within their department. """

    user = request.user

    # Ensure only managers can access this view
    if "Manager" not in user.profile.role:
        return render(request, "crm/403.html", status=403)  # Unauthorized access

    # Extract department from the role (e.g., "Manager - Wholesale" → "wholesale")
    department_name = user.profile.role.replace("Manager - ", "").lower()

    # Retrieve all salespeople under the managed department
    salespeople = Salesperson.objects.filter(customers__department=department_name).distinct()

    # Build the list of salesperson data
    salesperson_data = []
    for salesperson in salespeople:
        total_customers = Customer.objects.filter(salesperson=salesperson, department=department_name).count()
        total_contacts = Contact.objects.filter(customer__salesperson=salesperson, customer__department=department_name).count()
        total_sales = Customer.objects.filter(salesperson=salesperson, department=department_name).aggregate(Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
        avg_relationship_score = Contact.objects.filter(customer__salesperson=salesperson, customer__department=department_name).aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0

        salesperson_data.append({
            "username": salesperson.user.username,
            "full_name": salesperson.user.get_full_name(),
            "role": "Salesperson",  # Always a salesperson
            "total_customers": total_customers,
            "total_contacts": total_contacts,
            "total_sales": f"${total_sales:,.0f}",  # Format with commas
            "avg_relationship_score": round(avg_relationship_score, 2) if avg_relationship_score else "N/A"
        })

    return render(request, "crm/manager_dashboard.html", {"salesperson_data": salesperson_data, "department_name": department_name.capitalize()})
