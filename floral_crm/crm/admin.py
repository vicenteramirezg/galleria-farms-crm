from django.contrib import admin
from django.contrib import messages
from django.conf import settings
from .models import Salesperson, Customer, Contact, Profile
from crm.management.commands.send_welcome_email import Command as SendWelcomeCommand  # ✅ Import the management command

# ✅ Admin Action: Send Welcome Email for Salespersons
def send_welcome_email_admin(modeladmin, request, queryset):
    """ Admin action to trigger the send_welcome_email command for selected Salespersons """
    command = SendWelcomeCommand()  # Initialize the management command class
    count = 0  # Track how many emails were sent

    for salesperson in queryset:
        user = salesperson.user  # ✅ Get the associated User from Salesperson model
        if user.email:  # Ensure the user has a valid email
            command.handle(email=user.email)  # ✅ Call handle() and pass the email
            count += 1

    modeladmin.message_user(request, f"✅ Welcome emails sent to {count} salesperson(s)!", messages.SUCCESS)

send_welcome_email_admin.short_description = "📩 Send Welcome Email to Selected Salespersons"

# ✅ Register Salesperson Model with Custom Admin Action
@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('user__username',)
    actions = [send_welcome_email_admin]  # ✅ Attach the action to Salespersons!

# ✅ Register Other Models (No Changes Needed)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'role')
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

    # ✅ Make relationship_score, birthday_month, and birthday_day optional in admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["relationship_score"].required = False
        form.base_fields["birthday_month"].required = False
        form.base_fields["birthday_day"].required = False
        return form
