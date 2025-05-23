from django.contrib import admin
from django.urls import path
from .views import Index, SignUpView, CustomLogoutView, CustomLoginView, Dashboard, AddItem, EditItem, DeleteItem
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("dashboard/", Dashboard.as_view(), name="dashboard"),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name='edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name='delete-item'),
    path("signup/", SignUpView.as_view(), name="signup"),
    path('login/', CustomLoginView.as_view(template_name='inventory/login.html'), name='login'),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
]