from django.contrib import admin
from .models import Salesperson, Customer, Contact, Profile

# ✅ Register Profile Model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'role')
    ordering = ('user__username',)  

# ✅ Register Salesperson Model
@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at', 'updated_at')  
    search_fields = ('user__username', 'user__email', 'phone')

    # Ensure 'created_at' exists before using it as a filter
    list_filter = ('created_at',) if hasattr(Salesperson, 'created_at') else ()
    ordering = ('user__username',)

# ✅ Register Customer Model
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimated_yearly_sales', 'salesperson', 'created_at')
    search_fields = ('name', 'salesperson__user__username', 'salesperson__phone')

    # Ensure 'created_at' exists before using it as a filter
    list_filter = ('salesperson', 'created_at') if hasattr(Customer, 'created_at') else ()
    ordering = ('name',)

# ✅ Register Contact Model
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'customer', 'relationship_score', 'created_at')
    search_fields = ('name', 'email', 'phone', 'customer__name')

    # Ensure 'created_at' exists before using it as a filter
    list_filter = ('customer', 'relationship_score', 'created_at') if hasattr(Contact, 'created_at') else ()
    ordering = ('name',)
