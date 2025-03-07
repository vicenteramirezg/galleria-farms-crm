from django.contrib import admin
from .models import Salesperson, Customer, Contact, Profile

# ✅ Register Profile Model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'role')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')  # Prevents manual edits
    ordering = ('user__username',)

# ✅ Register Salesperson Model
@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('user__username',)

# ✅ Register Customer Model
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'estimated_yearly_sales', 'salesperson', 'created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('name', 'salesperson__user__username', 'salesperson__phone')
    list_filter = ('salesperson', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('name',)

# ✅ Register Contact Model
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'customer', 'relationship_score', 'created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('name', 'email', 'phone', 'customer__name', 'customer__salesperson__user__username')
    list_filter = ('customer', 'relationship_score', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('name',)
