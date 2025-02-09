from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView
from .models import Customer, Contact, Salesperson

def home(request):
    return render(request, 'home.html')

class SalespersonAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.salesperson.customers.filter(id=kwargs.get('customer_id')).exists():
            raise PermissionDenied("You do not have access to this customer.")
        return super().dispatch(request, *args, **kwargs)
    
@login_required
def dashboard(request):
    try:
        # Check if the user has a Salesperson object
        salesperson = request.user.salesperson
        customers = salesperson.customers.all()
    except Salesperson.DoesNotExist:
        # If the user doesn't have a Salesperson object, show all customers (for executives/admins)
        customers = Customer.objects.all()

    return render(request, 'crm/dashboard.html', {'customers': customers})

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'estimated_yearly_sales']
    template_name = 'crm/customer_form.html'
    success_url = '/dashboard/'

    def get_queryset(self):
        return self.request.user.salesperson.customers.all()

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    fields = ['name', 'phone', 'email', 'relationship_score']
    template_name = 'crm/contact_form.html'
    success_url = '/dashboard/'

    def get_queryset(self):
        return Contact.objects.filter(customer__salesperson=self.request.user.salesperson)
    
@login_required
def export_contacts_csv(request):
    # Get the salesperson's contacts
    contacts = Contact.objects.filter(customer__salesperson=request.user.salesperson)

    # Create the HttpResponse object with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Customer', 'Relationship Score'])

    # Write data rows
    for contact in contacts:
        writer.writerow([contact.name, contact.phone, contact.email, contact.customer.name, contact.relationship_score])

    return response