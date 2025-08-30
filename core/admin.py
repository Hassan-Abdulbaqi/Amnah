from django.contrib import admin
from .models import Partner, Order


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "joined_amount", "percentage")
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "order_type", "price", "date")
    list_filter = ("order_type", "date")
    search_fields = ("name", "description")
