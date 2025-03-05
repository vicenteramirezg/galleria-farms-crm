from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import csv
from django.db.models import Sum, Avg, Count
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import Customer, Contact, Salesperson, Profile, Role
from django.contrib.auth import login, logout
from .forms import CustomerForm, ContactForm, SignupForm  # Ensure you have this form
from django.http import HttpResponseNotAllowed
from django.utils.decorators import method_decorator
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)  # Setup logging for debugging

def home(request):
    return render(request, 'home.html')

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

@login_required
def dashboard(request):
    """ Generates summary metrics for Executives (all customers) & Salespersons (own customers). """

    if request.user.profile.role == Role.EXECUTIVE:  # ✅ Executives see all customers
        customers = Customer.objects.all().prefetch_related("contacts")
    else:  # ✅ Salespersons see only their own customers
        customers = Customer.objects.filter(salesperson=request.user.salesperson) \
                                    .prefetch_related("contacts")

    # Calculate key statistics
    total_sales = customers.aggregate(Sum("estimated_yearly_sales"))["estimated_yearly_sales__sum"] or 0
    total_contacts = Contact.objects.filter(customer__in=customers).count()
    avg_relationship_score = Contact.objects.filter(customer__in=customers) \
                                            .aggregate(Avg("relationship_score"))["relationship_score__avg"] or 0

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
            "avg_score": avg_score
        })

    return render(request, "crm/dashboard.html", {
        "customers": customer_data,
        "total_sales": total_sales,
        "total_contacts": total_contacts,
        "avg_relationship_score": round(avg_relationship_score, 2),
        "top_customers": top_customers
    })

class CustomerUpdateView(LoginRequiredMixin, SalespersonAccessMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    success_url = reverse_lazy('crm:customer_list')

    def get_queryset(self):
        """ Ensure the salesperson can only edit their own customers """
        queryset = Customer.objects.filter(salesperson=self.request.user.salesperson)
        logger.info(f"CustomerEditView - Filtering customers for salesperson {self.request.user.salesperson}: {queryset}")
        return queryset

    def form_valid(self, form):
        """ Ensure salesperson remains unchanged and log the exact form data received """
        form.instance.salesperson = self.request.user.salesperson  # Keep salesperson unchanged

        # 🛑 Log the form's raw input data
        logger.info(f"🔹 Form Data Before Saving: {form.cleaned_data}")

        response = super().form_valid(form)

        # 🔥 Fetch updated customer directly from the database to verify
        updated_customer = get_object_or_404(Customer, id=form.instance.id)
        logger.info(f"✅ Database After Update: {updated_customer.name}, Sales: {updated_customer.estimated_yearly_sales}")

        return response

    def form_invalid(self, form):
        """ Log invalid form submissions """
        logger.error(f"CustomerEditView - FORM INVALID: {form.errors}")
        return super().form_invalid(form)

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm  
    template_name = 'crm/contact_form.html'
    success_url = reverse_lazy('crm:contact_list')

    def get_queryset(self):
        """ Ensure the user can only edit their own contacts """
        return Contact.objects.filter(customer__salesperson=self.request.user.salesperson)

    def form_valid(self, form):
        """ Ensure the customer is always set automatically """
        contact = form.save(commit=False)
        contact.customer = self.get_object().customer  # Keep the original customer

        logger.info(f"Updating Contact ID: {contact.id}")  # Debugging
        logger.info(f"New Name: {form.cleaned_data.get('name')}")
        logger.info(f"New Email: {form.cleaned_data.get('email')}")
        logger.info(f"New Phone: {form.cleaned_data.get('phone')}")
        logger.info(f"New Relationship Score: {form.cleaned_data.get('relationship_score')}")
        logger.info(f"Keeping Customer ID: {contact.customer.id}")  # Debugging

        contact.save()  # ✅ Save the changes
        messages.success(self.request, "Contact updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        """ Log errors if the form is invalid """
        messages.error(self.request, "There were errors updating the contact.")
        logger.error(f"FORM INVALID ERRORS: {form.errors}")  # Debugging
        return super().form_invalid(form)


@login_required
def export_contacts(request):
    """ Exports contacts into a CSV file with additional fields: Birthday & Salesperson """

    # Get contacts associated with the logged-in salesperson
    contacts = Contact.objects.filter(customer__salesperson=request.user.salesperson)

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    # Set up the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Customer', 'Relationship Score', 'Birthday', 'Salesperson'])

    # Write contact data to CSV
    for contact in contacts:
        writer.writerow([
            contact.name,
            contact.phone,
            contact.email,
            contact.customer.name if contact.customer else "N/A",  # Handle missing customer
            contact.relationship_score,
            contact.birthday.strftime('%Y-%m-%d') if contact.birthday else "Not provided",  # Format birthday
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
    """ Fetch customers, group them by department, and order them alphabetically """
    customers = Customer.objects.filter(salesperson=request.user.salesperson).order_by('department', 'name')

    # Group customers by department
    grouped_customers = defaultdict(list)
    for customer in customers:
        grouped_customers[customer.department].append(customer)

    return render(request, 'crm/customer_list.html', {'grouped_customers': dict(grouped_customers)})

@login_required
def contact_list(request):
    """ Groups contacts by department → customer → ordered contacts """
    
    # Fetch all customers with contacts under the logged-in salesperson, ordered by department and name
    customers = Customer.objects.filter(salesperson=request.user.salesperson) \
                                .prefetch_related('contacts') \
                                .order_by("department", "name")

    grouped_contacts = defaultdict(list)

    # Organize customers under their respective departments
    for customer in customers:
        grouped_contacts[customer.department].append(customer)

    return render(request, "crm/contact_list.html", {"grouped_contacts": dict(grouped_contacts)})

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'crm/contact_list.html'  # Your template for displaying contacts
    context_object_name = 'contacts'  # Name used for the context in the template

    def get_queryset(self):
        # Filter contacts by the logged-in salesperson
        return Contact.objects.filter(customer__salesperson=self.request.user.salesperson)

@login_required
def add_contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.phone = form.cleaned_data['phone']  # Ensure phone is stored
            contact.save()
            return redirect("crm:contact_list")
    else:
        form = ContactForm()
    
    return render(request, "crm/add_contact.html", {"form": form})

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
        
        # ✅ Fix: Use Avg from django.db.models
        avg_relationship_score = contacts.aggregate(avg_score=Avg("relationship_score"))["avg_score"]

        context.update({
            "contacts": contacts,
            "avg_relationship_score": avg_relationship_score if avg_relationship_score else "No scores yet",
        })
        return context
