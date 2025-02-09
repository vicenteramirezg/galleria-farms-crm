from django.urls import path
from . import views
from .views import CustomerUpdateView, ContactUpdateView

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('customer/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('contact/<int:pk>/edit/', ContactUpdateView.as_view(), name='contact_edit'),
    path('export-contacts/', views.export_contacts_csv, name='export_contacts'),
]