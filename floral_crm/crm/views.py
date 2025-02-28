from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import csv
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from .models import Customer, Contact, Salesperson, Profile, Role
from django.contrib.auth import login, logout
from .forms import CustomerForm, ContactForm, SignupForm  # Ensure you have this form
from django.http import HttpResponseNotAllowed
from django.utils.decorators import method_decorator

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
    user_profile = request.user.profile

    if user_profile.is_executive():
        customers = Customer.objects.all()  # Executives see all customers
    else:
        try:
            salesperson = request.user.salesperson
            customers = salesperson.customers.all()
        except AttributeError:
            customers = Customer.objects.none()

    return render(request, 'crm/dashboard.html', {'customers': customers})

class CustomerUpdateView(LoginRequiredMixin, SalespersonAccessMixin, UpdateView):
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

@login_required
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

@login_required
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

@login_required
def customer_list(request):
    customers = Customer.objects.filter(salesperson=request.user.salesperson)
    return render(request, 'crm/customer_list.html', {'customers': customers})

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
            contact.customer.salesperson = request.user.salesperson  # Assign salesperson
            contact.save()
            return redirect(reverse('crm:contact_list'))
    else:
        form = ContactForm()
    
    return render(request, 'crm/add_contact.html', {'form': form})