from django.urls import path
from . import views
from .views import dashboard, CustomerUpdateView, ContactUpdateView, add_customer, CustomerDetailView, gift_planning, gift_tracking, gifts_list, add_gift  # Make sure add_customer is imported

app_name = 'crm'  # Add this line to set a namespace for your app

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('customer/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('contact/<int:pk>/edit/', ContactUpdateView.as_view(), name='contact_edit'),
    path('export-contacts/', views.export_contacts, name='export_contacts'),
    path('export-customers/', views.export_customers, name='export_customers'),
    path('customers/', views.customer_list, name='customer_list'),
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/add/', views.add_contact, name='add_contact'),
    path('customers/add/', views.add_customer, name='add_customer'),  # Add this line to map the URL for add_customer
    path("customer/<int:pk>/", CustomerDetailView.as_view(), name="customer_detail"),  # ✅ Correct
    path('executive-dashboard/', views.executive_dashboard, name='executive_dashboard'),
    path("manager-dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("update_user_role/", views.update_user_role, name="update_user_role"),
    path("gifts/", views.gift_season_dashboard, name="gift_season_dashboard"),
    path("gifts/create/", views.create_gift_season, name="create_gift_season"),  # New AJAX URL
    path("gifts/<int:season_id>/planning/", views.gift_planning, name="gift_planning"),
    path("gifts/<int:season_id>/tracking/", views.gift_tracking, name="gift_tracking"),
    path("gifts/list/", views.gifts_list, name="gifts_list"),
    path("gifts/add/", views.add_gift, name="add_gift"),
]
