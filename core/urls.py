from django.urls import path
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard/export/", views.dashboard_export, name="dashboard_export"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("logs/", views.logs_list, name="logs_list"),
    path("orders/", views.orders_list, name="orders_list"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<int:pk>/edit/", views.order_edit, name="order_edit"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),
    path("partners/", views.partners_list, name="partners_list"),
    path("partners/new/", views.partner_create, name="partner_create"),
    path("partners/<int:pk>/edit/", views.partner_edit, name="partner_edit"),
    path("partners/<int:pk>/delete/", views.partner_delete, name="partner_delete"),
]


