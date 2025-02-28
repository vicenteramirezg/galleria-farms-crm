from django.contrib import admin
from .models import Salesperson, Customer, Contact, Profile

# Register your models here
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Display user and role in admin
    list_filter = ('role',)
    search_fields = ('user__username', 'role')

@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')  # Fields to display in the admin list view
    search_fields = ('user__username', 'phone')  # Fields to search by

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimated_yearly_sales', 'salesperson')
    search_fields = ('name', 'salesperson__user__username')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'customer', 'relationship_score')
    search_fields = ('name', 'email', 'customer__name')