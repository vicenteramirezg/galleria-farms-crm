from django.contrib import admin
from .models import Salesperson, Customer, Contact, Profile

# ✅ Register Profile Model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Display user and role in admin panel
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'role')  # Added email for better searchability
    ordering = ('user__username',)  # Ensure results are ordered properly

# ✅ Register Salesperson Model
@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at', 'updated_at')  # Added timestamps for tracking
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at',)  # Allow filtering by creation date
    ordering = ('user__username',)

# ✅ Register Customer Model
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimated_yearly_sales', 'salesperson', 'created_at')
    search_fields = ('name', 'salesperson__user__username', 'salesperson__phone')
    list_filter = ('salesperson', 'created_at')  # Filter by salesperson
    ordering = ('name',)

# ✅ Register Contact Model
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'customer', 'relationship_score', 'created_at')
    search_fields = ('name', 'email', 'phone', 'customer__name', 'customer__salesperson__user__username')
    list_filter = ('customer', 'relationship_score', 'created_at')  # Added filtering by customer and score
    ordering = ('name',)
