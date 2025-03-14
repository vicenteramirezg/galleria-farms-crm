# Django core imports
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView, DetailView
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.paginator import Paginator

# Django database and utility imports
from django.db.models import Sum, Avg, Count, Q
from django.db.models.functions import ExtractMonth, ExtractDay

# Models and forms
from .models import Customer, Contact, Salesperson, Profile, Role, Gift, GiftAssignment, GiftSeason, GiftAssignmentStatus
from .forms import CustomerForm, ContactForm, SignupForm, GiftAssignmentForm, GiftSeasonForm  # Ensure you have this form

# Python standard library imports
import csv
from collections import defaultdict
import logging
from datetime import timedelta, date, datetime
import json

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
    """🚀 Optimized dashboard with accurate total sales, contacts, and indexed queries."""
    User = get_user_model()
    user = request.user
    salesperson = getattr(user, 'salesperson', None)

    # **🚀 Fetch Filter Parameters**
    selected_department = request.GET.get("department", "").strip()
    selected_salesperson = request.GET.get("salesperson", "").strip()
    selected_salesperson = int(selected_salesperson) if selected_salesperson.isdigit() else None

    # **🚀 Indexed Query: Filter Customers Efficiently**
    customers_query = Customer.objects.order_by("-estimated_yearly_sales")

    if user.profile.role == Role.EXECUTIVE:
        customers = customers_query
    elif "Manager" in user.profile.role:
        department_name = user.profile.role.replace("Manager - ", "").lower()
        customers = customers_query.filter(department=department_name)
    else:
        customers = customers_query.filter(salesperson=salesperson)

    # **🚀 Apply Additional Filters**
    if selected_department:
        customers = customers.filter(department=selected_department)
    if selected_salesperson:
        salesperson_id = User.objects.filter(id=selected_salesperson).values_list("salesperson__id", flat=True).first()
        if salesperson_id:
            customers = customers.filter(salesperson_id=salesperson_id)

    # **🚀 Correctly Compute Total Sales**
    total_sales = customers.aggregate(total_sales=Sum("estimated_yearly_sales"))["total_sales"] or 0

    # **🚀 Correctly Compute Total Contacts Count**
    total_contacts = Contact.objects.filter(customer__in=customers, is_active=True).count()

    # **🚀 Correctly Compute Avg Relationship Score**
    avg_relationship_score = Contact.objects.filter(customer__in=customers, is_active=True) \
        .aggregate(avg_score=Avg("relationship_score"))["avg_score"] or 0

    # **🚀 Fetch Top Customers (Includes Estimated Sales)**
    top_customers = customers.annotate(
        num_contacts=Count("contacts", filter=Q(contacts__is_active=True)),
        avg_score=Avg("contacts__relationship_score", filter=Q(contacts__is_active=True))
    ).values("id", "name", "estimated_yearly_sales", "num_contacts", "avg_score")[:10]

    # **🚀 Upcoming Birthdays Query**
    today = date.today()
    future_date = today + timedelta(days=30)

    upcoming_birthdays = Contact.objects.filter(
        customer__in=customers,
        is_active=True
    ).filter(
        Q(birthday_month=today.month, birthday_day__gte=today.day) |
        Q(birthday_month=future_date.month, birthday_day__lte=future_date.day) |
        Q(birthday_month__gt=today.month, birthday_month__lt=future_date.month)
    ).order_by("birthday_month", "birthday_day").only("name", "birthday_month", "birthday_day", "customer")

    # **🚀 Format Birthdays Efficiently**
    for contact in upcoming_birthdays:
        month_name = MONTH_NAMES.get(contact.birthday_month, "Unknown")
        contact.clean_birthday = f"{month_name}, {contact.birthday_day}"

    # **🚀 Fetch Departments & Available Salespeople**
    department_choices = dict(Customer.DEPARTMENT_CHOICES)

    available_salespeople = User.objects.filter(
        salesperson__customers__isnull=False
    ).distinct().only("id", "first_name", "last_name")

    return render(request, "crm/dashboard.html", {
        "customers": top_customers,  # ✅ Now includes estimated sales correctly
        "total_sales": f"{total_sales:,.0f}",
        "total_contacts": total_contacts,
        "avg_relationship_score": round(avg_relationship_score, 2) if avg_relationship_score else "N/A",
        "top_customers": top_customers,
        "upcoming_birthdays": upcoming_birthdays,
        "department_choices": department_choices,
        "available_salespeople": available_salespeople,
        "selected_department": selected_department,
        "selected_salesperson": selected_salesperson,
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
                "Manager - International": Customer.INTERNATIONAL,
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
                "Manager - International": Customer.INTERNATIONAL,
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
                "Manager - International": Customer.INTERNATIONAL,
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
                "Manager - International": Customer.INTERNATIONAL,
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
    """🚀 Export filtered contacts based on user role and active filters."""
    
    user = request.user
    selected_department = request.GET.get("department", "").strip()
    selected_salesperson = request.GET.get("salesperson", "").strip()
    selected_status = request.GET.get("status", "").strip()
    search_query = request.GET.get("search", "").strip()

    # 🚀 Fetch customers based on user role
    customers_query = Customer.objects.order_by("name")

    if user.profile.role == Role.EXECUTIVE:
        customers = customers_query  # ✅ Executives can export all contacts

    elif user.profile.role == Role.SALESPERSON:
        customers = customers_query.filter(salesperson=user.salesperson)  # ✅ Salespeople only export their own customers' contacts

    else:  # ✅ Managers can export contacts from their department
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
            Role.MANAGER_INTERNATIONAL: Customer.INTERNATIONAL,
        }
        department = department_mapping.get(user.profile.role)
        customers = customers_query.filter(department=department) if department else Customer.objects.none()

    # 🚀 Apply additional filters
    if selected_department:
        customers = customers.filter(department=selected_department)
    if selected_salesperson:
        customers = customers.filter(salesperson_id=selected_salesperson)

    # 🚀 Fetch contacts based on filtered customers
    contacts = Contact.objects.filter(customer__in=customers)

    # 🚀 Apply contact-specific filters
    if selected_status == "active":
        contacts = contacts.filter(is_active=True)
    elif selected_status == "inactive":
        contacts = contacts.filter(is_active=False)

    if search_query:
        contacts = contacts.filter(name__icontains=search_query)

    # 🚀 Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_contacts.csv"'

    # 🚀 Set up the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Customer', 'Department', 'Relationship Score', 'Birthday Month', 'Birthday Day', 'Salesperson'])

    # 🚀 Write filtered contact data to CSV
    for contact in contacts:
        writer.writerow([
            contact.name,
            contact.phone if contact.phone else "N/A",
            contact.email if contact.email else "N/A",
            contact.customer.name if contact.customer else "N/A",
            contact.customer.get_department_display() if contact.customer else "N/A",  # Fetch department name
            contact.relationship_score,
            contact.get_birthday_month_display() if contact.birthday_month else "Not provided",
            contact.birthday_day if contact.birthday_day else "Not provided",
            contact.customer.salesperson.user.get_full_name() if contact.customer and contact.customer.salesperson else "N/A"
        ])

    return response

@login_required
def export_customers(request):
    """🚀 Export filtered customers based on user role and active filters."""
    
    user = request.user
    selected_department = request.GET.get("department", "").strip()
    selected_salesperson = request.GET.get("salesperson", "").strip()
    search_query = request.GET.get("search", "").strip()

    # 🚀 Determine which customers the user is allowed to export
    if user.profile.role == Role.EXECUTIVE:
        customers = Customer.objects.all()  # ✅ Executives export all customers

    elif "Manager" in user.profile.role:
        # ✅ Managers: Export customers only from their department
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
            Role.MANAGER_INTERNATIONAL: Customer.INTERNATIONAL,
        }
        department = department_mapping.get(user.profile.role, None)
        customers = Customer.objects.filter(department=department) if department else Customer.objects.none()

    elif user.profile.role == Role.SALESPERSON:
        # ✅ Salespeople: Export only their own customers
        customers = Customer.objects.filter(salesperson=user.salesperson)

    else:
        return HttpResponse("You are not authorized to export customers.", status=403)

    # 🚀 Apply active filters from GET parameters
    if selected_department:
        customers = customers.filter(department=selected_department)
    if selected_salesperson:
        customers = customers.filter(salesperson_id=selected_salesperson)
    if search_query:
        customers = customers.filter(name__icontains=search_query)

    # 🚀 Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_customers.csv"'

    # 🚀 Set up the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Department', 'Estimated Yearly Sales', 'Salesperson'])

    # 🚀 Write filtered customer data to CSV
    for customer in customers:
        writer.writerow([
            customer.name,
            customer.get_department_display(),  # ✅ Human-readable department name
            f"${customer.estimated_yearly_sales:,.0f}",  # ✅ Format sales
            customer.salesperson.user.get_full_name() if customer.salesperson else "N/A"  # ✅ Salesperson name
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
    """🚀 Optimized customer list view with pagination by customers, grouped by department, and sorting."""
    
    user = request.user
    selected_department = request.GET.get("department", "").strip()
    selected_salesperson = request.GET.get("salesperson", "").strip()
    search_query = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "name")  # Default sorting: name
    order = request.GET.get("order", "asc")  # Default order: ascending

    # **🚀 Start with All Customers (Ordered by Department & Name)**
    customers_query = Customer.objects.order_by("department", "name")

    # **🚀 Apply Role-Based Filtering**
    if user.profile.role == Role.EXECUTIVE:
        customers = customers_query  # ✅ Executives see all customers
    elif user.profile.role == Role.SALESPERSON:
        customers = customers_query.filter(salesperson=user.salesperson)  # ✅ Salespeople see their own customers
    else:  # ✅ Managers see only their department
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
            Role.MANAGER_INTERNATIONAL: Customer.INTERNATIONAL,
        }
        department = department_mapping.get(user.profile.role, None)
        customers = customers_query.filter(department=department) if department else Customer.objects.none()

    # **🚀 Apply Filters**
    if selected_department:
        customers = customers.filter(department=selected_department)
    if selected_salesperson:
        customers = customers.filter(salesperson_id=selected_salesperson)
    if search_query:
        customers = customers.filter(name__icontains=search_query)

    # **🚀 Sorting Logic (Ensure annotation exists before ordering)**
    sort_options = {
        "name": "name",
        "department": "department",  # ✅ Added department sorting
        "estimated_yearly_sales": "estimated_yearly_sales",
        "avg_relationship_score": "avg_relationship_score_annotated",  # ✅ Using annotation name
        "salesperson": "salesperson__user__first_name",  # ✅ Sort by Salesperson's first name
    }

    # **🚀 Apply annotation before sorting**
    customers = customers.annotate(
        avg_relationship_score_annotated=Avg("contacts__relationship_score")  # Rename annotation
    ).select_related("salesperson__user").only("id", "name", "department", "estimated_yearly_sales", "salesperson")

    if sort in sort_options:
        sort_field = sort_options[sort]
        if order == "desc":
            sort_field = f"-{sort_field}"  # Apply descending order
        customers = customers.order_by(sort_field)

    # **🚀 Optimize Query Execution**
    customers = customers.select_related("salesperson__user").annotate(
        avg_relationship_score=Avg("contacts__relationship_score")
    ).only("id", "name", "department", "estimated_yearly_sales", "salesperson")

    # **🚀 Fetch all customers into a list for pagination**
    customer_list = list(customers)

    # **🚀 Pagination by Customers**
    paginator = Paginator(customer_list, 20)  # ✅ Show 20 customers per page
    page_number = request.GET.get("page")
    customers_paginated = paginator.get_page(page_number)

    # **🚀 Regroup Paginated Customers by Department**
    grouped_customers = defaultdict(list)
    for customer in customers_paginated:
        grouped_customers[customer.get_department_display()].append(customer)

    # **🚀 Optimize Salespeople Query**
    available_salespeople = Salesperson.objects.filter(
        customers__isnull=False
    ).distinct().only("id", "user__first_name", "user__last_name").order_by("user__first_name", "user__last_name")

    return render(request, "crm/customer_list.html", {
        "grouped_customers_paginated": grouped_customers.items(),
        "customers_paginated": customers_paginated,
        "department_choices": dict(Customer.DEPARTMENT_CHOICES),
        "available_salespeople": available_salespeople,
        "selected_department": selected_department,
        "selected_salesperson": selected_salesperson,
        "search_query": search_query,
        "sort": sort,  # ✅ Pass sort field to template
        "order": order,  # ✅ Pass order to template
    })

@login_required
def contact_list(request):
    """🚀 Optimized Contact List with Sorting, Pagination & Indexed Queries"""
    
    user = request.user
    selected_department = request.GET.get("department", "").strip()
    selected_salesperson = request.GET.get("salesperson", "").strip()
    selected_status = request.GET.get("status", "all").strip()
    search_query = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "customer")  # Default sort by customer
    order = request.GET.get("order", "asc")  # Default order is ascending
    page = request.GET.get("page", 1)

    # **🚀 Fetch Customers (Used for Filtering Contacts)**
    customers_query = Customer.objects.order_by("name")

    if user.profile.role == Role.EXECUTIVE:
        customers = customers_query  # ✅ Executives see all customers
    elif user.profile.role == Role.SALESPERSON:
        customers = customers_query.filter(salesperson=user.salesperson)  # ✅ Salespeople see their customers only
    else:
        department_mapping = {
            Role.MANAGER_MASS_MARKET: Customer.MASS_MARKET,
            Role.MANAGER_MM2: Customer.MM2,
            Role.MANAGER_ECOMMERCE: Customer.ECOMMERCE,
            Role.MANAGER_WHOLESALE: Customer.WHOLESALE,
            Role.MANAGER_INTERNATIONAL: Customer.INTERNATIONAL,
        }
        department = department_mapping.get(user.profile.role)
        customers = customers_query.filter(department=department) if department else Customer.objects.none()

    # **🚀 Apply Additional Customer Filters**
    if selected_department:
        customers = customers.filter(department=selected_department)
    if selected_salesperson:
        customers = customers.filter(salesperson_id=selected_salesperson)

    # **🚀 Fetch Contacts Efficiently**
    contacts_query = (
        Contact.objects
        .filter(customer__in=customers)
        .select_related("customer")  # Optimized join
        .annotate(avg_relationship_score=Avg("relationship_score"))  # For sorting
        .only("id", "name", "email", "phone", "birthday_day", "birthday_month", "relationship_score", "is_active", "customer__id", "customer__name")
    )

    # **🚀 Apply Contact Filters**
    if selected_status == "active":
        contacts_query = contacts_query.filter(is_active=True)
    elif selected_status == "inactive":
        contacts_query = contacts_query.filter(is_active=False)

    if search_query:
        contacts_query = contacts_query.filter(name__icontains=search_query)

    # **🚀 Sorting Logic**
    sort_options = {
        "customer": "customer__name",
        "contact_name": "name",
        "relationship_score": "avg_relationship_score",
    }

    if sort in sort_options:
        sort_field = sort_options[sort]
        if order == "desc":
            sort_field = f"-{sort_field}"
        contacts_query = contacts_query.order_by(sort_field)

    # **🚀 Pagination (20 contacts per page)**
    paginator = Paginator(contacts_query, 20)
    contacts_paginated = paginator.get_page(page)

    # **🚀 Organize Contacts by Customer**
    grouped_contacts = {}
    for contact in contacts_paginated:
        customer = contact.customer
        if customer not in grouped_contacts:
            grouped_contacts[customer] = []
        grouped_contacts[customer].append(contact)

    # **🚀 Fetch Department & Salespeople Filters**
    department_choices = dict(Customer.DEPARTMENT_CHOICES)
    available_salespeople = Salesperson.objects.filter(
        customers__isnull=False  # Ensures salesperson has customers
    ).select_related("user").distinct().order_by("user__first_name", "user__last_name")

    return render(request, "crm/contact_list.html", {
        "grouped_contacts": grouped_contacts,
        "contacts_paginated": contacts_paginated,
        "department_choices": department_choices,
        "available_salespeople": available_salespeople,
        "selected_department": selected_department,
        "selected_salesperson": selected_salesperson,
        "selected_status": selected_status,
        "search_query": search_query,
        "sort": sort,
        "order": order,
    })

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
            if request.user.profile.role == "Executive":
                contact.customer = form.cleaned_data["customer"]  # ✅ Executives can assign any customer
            elif request.user.profile.role == "Salesperson":
                if customer and customer.salesperson == request.user.salesperson:
                    contact.customer = customer  # ✅ Assign only if valid
                else:
                    messages.error(request, "You cannot add a contact to this customer.")
                    return redirect("crm:contact_list")  # 🚫 Prevent unauthorized assignment
            elif "Manager" in request.user.profile.role:
                department = request.user.profile.role.replace("Manager - ", "")
                if customer and customer.department == department:
                    contact.customer = customer  # ✅ Managers can assign contacts only within their department
                else:
                    messages.error(request, "You cannot add a contact to this customer.")
                    return redirect("crm:contact_list")

            contact.save()
            logger.info(f"✅ Contact Created: {contact.name} - Redirecting to customer {contact.customer.id}")

            # 🚀 **Fixed redirect**
            return HttpResponseRedirect(reverse("crm:customer_detail", args=[contact.customer.id]))  # ✅ Correct way to redirect
    else:
        # ✅ If customer exists, pre-fill the field. If not, allow selection.
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
@executive_required
def executive_dashboard(request):
    """ View for Executives to see an overview of all users and their performance. """
    
    users = Profile.objects.select_related("user").order_by("user__username")

    user_data = []
    for profile in users:
        salesperson = getattr(profile.user, "salesperson", None)

        if salesperson:
            total_customers = Customer.objects.filter(salesperson=salesperson).count()
            total_contacts = Contact.objects.filter(customer__salesperson=salesperson).count()
            total_sales = Customer.objects.filter(salesperson=salesperson).aggregate(Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
            avg_relationship_score = Contact.objects.filter(customer__salesperson=salesperson).aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0
        else:
            total_customers = total_contacts = total_sales = avg_relationship_score = "N/A"

        user_data.append({
            "id": profile.user.id,
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
@executive_required
def update_user_role(request):
    """ Allows Executives to update a user's role via AJAX. """
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_role = request.POST.get("new_role")

        if not user_id or not new_role:
            return JsonResponse({"success": False, "error": "Invalid data"})

        user_to_update = get_object_or_404(Profile, user_id=user_id)
        if new_role in [
            Role.EXECUTIVE, Role.MANAGER_MASS_MARKET, Role.MANAGER_MM2, 
            Role.MANAGER_ECOMMERCE, Role.MANAGER_WHOLESALE, Role.MANAGER_INTERNATIONAL, Role.SALESPERSON
        ]:
            user_to_update.role = new_role
            user_to_update.save()
            return JsonResponse({"success": True})
        
        return JsonResponse({"success": False, "error": "Invalid role selection"})

    return JsonResponse({"success": False, "error": "Invalid request method"})

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
    salespeople = Salesperson.objects.filter(customers__department=department_name).distinct().order_by("user__username")

    # Build the list of salesperson data
    salesperson_data = []
    for salesperson in salespeople:
        total_customers = Customer.objects.filter(salesperson=salesperson, department=department_name).count()
        total_contacts = Contact.objects.filter(customer__salesperson=salesperson, customer__department=department_name).count()
        total_sales = Customer.objects.filter(salesperson=salesperson, department=department_name).aggregate(
            Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
        avg_relationship_score = Contact.objects.filter(customer__salesperson=salesperson, customer__department=department_name).aggregate(
            Avg("relationship_score"))["relationship_score__avg"] or 0

        salesperson_data.append({
            "username": salesperson.user.username,
            "full_name": salesperson.user.get_full_name(),
            "role": "Salesperson",  # Always a salesperson
            "total_customers": total_customers,
            "total_contacts": total_contacts,
            "total_sales": f"${total_sales:,.0f}",  # Format with commas
            "avg_relationship_score": round(avg_relationship_score, 2) if avg_relationship_score else "N/A"
        })

    return render(request, "crm/manager_dashboard.html", {
        "salesperson_data": salesperson_data,
        "department_name": department_name.capitalize()
    })

def gift_planning(request, season_id):
    """ Assign gifts to contacts for a specific season """
    season = get_object_or_404(GiftSeason, id=season_id)

    # Fetch all active contacts & related customer/salesperson data
    contacts = Contact.objects.filter(is_active=True).select_related("customer", "customer__salesperson")

    # Fetch existing gift assignments for the selected season
    gift_assignments = GiftAssignment.objects.filter(gift_season=season)

    # ✅ Convert to dictionary for quick lookup
    assignments = {a.contact_id: a for a in gift_assignments}

    return render(request, "crm/gift_planning.html", {
        "season": season,
        "contacts": contacts,
        "assignments": assignments,  # ✅ Precomputed lookup
        "gifts": Gift.objects.all()
    })

def update_gift_assignment(request):
    """ AJAX view to update the Gift, Note, and Status for a contact """
    if request.method == "POST":
        data = json.loads(request.body)
        assignment_id = data.get("assignment_id")
        gift_id = data.get("gift_id")
        note = data.get("note", "").strip()
        status = data.get("status", "").strip()

        assignment = get_object_or_404(GiftAssignment, id=assignment_id)
        assignment.gift_id = gift_id
        assignment.note = note
        assignment.status = status
        assignment.save()

        return JsonResponse({
            "success": True,
            "gift": assignment.gift.name if assignment.gift else "No Gift",
            "note": assignment.note,
            "status": assignment.get_status_display()
        })

    return JsonResponse({"success": False})

def gift_tracking(request, season_id):
    """ View to track assigned gifts for a specific season """
    season = get_object_or_404(GiftSeason, id=season_id)
    assignments = GiftAssignment.objects.filter(gift_season=season).select_related("contact", "gift")

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("status_"):
                assignment_id = key.split("_")[1]
                assignment = get_object_or_404(GiftAssignment, id=assignment_id)
                assignment.status = value
                assignment.save()

        messages.success(request, "Gift statuses updated successfully!")
        return redirect("crm:gift_tracking", season_id=season.id)

    return render(request, "crm/gift_tracking.html", {"assignments": assignments, "season": season})

def gift_season_dashboard(request):
    """ Dashboard showing all available gift seasons & allowing new season creation """
    seasons = GiftSeason.objects.all().order_by("-date")  # Order by occasion date desc

    if request.method == "POST":
        form = GiftSeasonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Gift season created successfully!")
            return redirect("crm:gift_season_dashboard")

    else:
        form = GiftSeasonForm()

    return render(request, "crm/gift_season_dashboard.html", {"seasons": seasons, "form": form})

@csrf_exempt
def create_gift_season(request):
    """ Handles AJAX request to create a new Gift Season """
    if request.method == "POST":
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        date = data.get("date", "").strip()

        # Validate the inputs
        if name and date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                season = GiftSeason.objects.create(name=name, date=date)
                return JsonResponse({"success": True, "id": season.id, "name": season.name, "date": season.date.strftime("%B %d, %Y")})
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

    return JsonResponse({"success": False, "error": "Invalid data."})

def gifts_list(request):
    """ Display all available gifts """
    gifts = Gift.objects.all()
    return render(request, "crm/gifts_list.html", {"gifts": gifts})

def add_gift(request):
    """ Handle adding a new gift via AJAX """
    if request.method == "POST":
        data = json.loads(request.body)
        gift_name = data.get("name")

        if not gift_name:
            return JsonResponse({"success": False, "error": "Gift name is required."}, status=400)

        # ✅ Create new gift
        Gift.objects.create(name=gift_name)
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)
