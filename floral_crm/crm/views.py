from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import csv
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from .models import Customer, Contact, Salesperson
from django.contrib.auth import login
from .forms import SignupForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomerForm, ContactForm  # Ensure you have this form

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to a desired page after signup
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

class SalespersonAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.salesperson.customers.filter(id=kwargs.get('customer_id')).exists():
            raise PermissionDenied("You do not have access to this customer.")
        return super().dispatch(request, *args, **kwargs)

def dashboard(request):
    try:
        salesperson = request.user.salesperson
        customers = salesperson.customers.all()
    except Salesperson.DoesNotExist:
        customers = Customer.objects.all()

    return render(request, 'crm/dashboard.html', {'customers': customers})

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'estimated_yearly_sales']
    template_name = 'crm/customer_form.html'
    success_url = reverse_lazy('crm:dashboard')

    def get_queryset(self):
        return self.request.user.salesperson.customers.all()

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    fields = ['name', 'phone', 'email', 'relationship_score']
    template_name = 'crm/contact_form.html'
    success_url = reverse_lazy('crm:dashboard')

    def get_queryset(self):
        return Contact.objects.filter(customer__salesperson=self.request.user.salesperson)

def export_contacts(request):
    contacts = Contact.objects.filter(customer__salesperson=request.user.salesperson)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Customer', 'Relationship Score'])

    for contact in contacts:
        writer.writerow([contact.name, contact.phone, contact.email, contact.customer.name, contact.relationship_score])

    return response

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    success_url = reverse_lazy('crm:dashboard')

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.salesperson = self.request.user.salesperson
        customer.save()
        return super().form_valid(form)

def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.salesperson = request.user.salesperson  # Assign salesperson
            customer.save()
            return redirect(reverse('crm:dashboard'))  # Use 'crm:dashboard' with the namespace
    else:
        form = CustomerForm()
    
    return render(request, 'crm/add_customer.html', {'form': form})

def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'crm/customer_list.html', {'customers': customers})

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'crm/contact_list.html'  # Your template for displaying contacts
    context_object_name = 'contacts'  # Name used for the context in the template

    def get_queryset(self):
        # Filter contacts by the logged-in salesperson
        return Contact.objects.filter(customer__salesperson=self.request.user.salesperson)

def add_contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.salesperson = request.user.salesperson  # Assign salesperson if needed
            contact.save()
            return redirect(reverse('crm:contact_list'))
    else:
        form = ContactForm()
    
    return render(request, 'crm/add_contact.html', {'form': form})