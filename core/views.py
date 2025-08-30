from decimal import Decimal
from django.db.models import Sum, Case, When, F, BigIntegerField
from django.shortcuts import render, redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

from .models import Order, Partner, ActivityLog
from .forms import OrderForm, PartnerForm, OrderFilterForm, DashboardFilterForm
from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django import forms as django_forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def log_activity(request, action: str, instance=None, *, model_name: str = None, object_id=None, object_repr: str = None, details: str = "") -> None:
    if instance is not None:
        model_name = instance.__class__.__name__
        object_id = getattr(instance, "pk", None)
        object_repr = str(instance)
    ActivityLog.objects.create(
        user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action,
        model_name=model_name or "",
        object_id=object_id or 0,
        object_repr=object_repr or "",
        details=details or "",
    )

@login_required
def dashboard(request):
    form = DashboardFilterForm(request.GET or None)

    qs = Order.objects.all()
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

    totals = qs.aggregate(
        total_ingoing=Sum(Case(When(order_type=Order.INGOING, then=F("price")), output_field=BigIntegerField())),
        total_outgoing=Sum(Case(When(order_type=Order.OUTGOING, then=F("price")), output_field=BigIntegerField())),
    )
    total_ingoing = totals.get("total_ingoing") or 0
    total_outgoing = totals.get("total_outgoing") or 0
    total_profit = total_ingoing - total_outgoing

    num_orders = qs.count()
    num_ingoing = qs.filter(order_type=Order.INGOING).count()
    num_outgoing = qs.filter(order_type=Order.OUTGOING).count()

    partners = list(Partner.objects.all())
    partner_rows = []
    for partner in partners:
        share = (Decimal(total_profit) * (partner.percentage or Decimal("0"))) / Decimal("100")
        partner_rows.append({
            "partner": partner,
            "share": share,
        })

    context = {
        "filter_form": form,
        "total_ingoing": total_ingoing,
        "total_outgoing": total_outgoing,
        "total_profit": total_profit,
        "num_orders": num_orders,
        "num_ingoing": num_ingoing,
        "num_outgoing": num_outgoing,
        "partner_rows": partner_rows,
    }
    return render(request, "dashboard.html", context)


@login_required
def dashboard_export(request):
    form = DashboardFilterForm(request.GET or None)
    qs = Order.objects.all()
    date_from = None
    date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

    totals = qs.aggregate(
        total_ingoing=Sum(Case(When(order_type=Order.INGOING, then=F("price")), output_field=BigIntegerField())),
        total_outgoing=Sum(Case(When(order_type=Order.OUTGOING, then=F("price")), output_field=BigIntegerField())),
    )
    total_ingoing = totals.get("total_ingoing") or 0
    total_outgoing = totals.get("total_outgoing") or 0
    total_profit = total_ingoing - total_outgoing

    num_orders = qs.count()
    num_ingoing = qs.filter(order_type=Order.INGOING).count()
    num_outgoing = qs.filter(order_type=Order.OUTGOING).count()

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = "attachment; filename=dashboard_stats.csv"

    writer = csv.writer(response)
    # Summary section
    writer.writerow(["Dashboard Statistics"])
    writer.writerow(["Date From", date_from or "-"])
    writer.writerow(["Date To", date_to or "-"])
    writer.writerow(["Total Ingoing", total_ingoing])
    writer.writerow(["Total Outgoing", total_outgoing])
    writer.writerow(["Total Profit", total_profit])
    writer.writerow(["Orders Count", num_orders])
    writer.writerow(["Ingoing Count", num_ingoing])
    writer.writerow(["Outgoing Count", num_outgoing])
    writer.writerow([])

    # Partner shares
    writer.writerow(["Partner Shares (from profit)"])
    writer.writerow(["Partner", "Percentage", "Share Amount"])
    for partner in Partner.objects.all():
        share = (Decimal(total_profit) * (partner.percentage or Decimal("0"))) / Decimal("100")
        writer.writerow([partner.name, f"{partner.percentage}%", share])
    writer.writerow([])

    # Orders detail
    writer.writerow(["Orders"])
    writer.writerow(["Date", "Name", "Type", "Price", "Description"])
    for order in qs.order_by("-date", "name"):
        writer.writerow([order.date, order.name, order.get_order_type_display(), order.price, order.description])

    return response


@login_required
def orders_list(request):
    qs = Order.objects.all()
    form = OrderFilterForm(request.GET or None)

    if form.is_valid():
        search = form.cleaned_data.get("search")
        order_type = form.cleaned_data.get("order_type")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        price_min = form.cleaned_data.get("price_min")
        price_max = form.cleaned_data.get("price_max")
        sort_by = form.cleaned_data.get("sort_by") or "-date"

        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if order_type:
            qs = qs.filter(order_type=order_type)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by("-date")

    # Pagination
    per_page_default = 10
    try:
        per_page = int((form.data.get("per_page") or form.cleaned_data.get("per_page") or per_page_default))
    except Exception:
        per_page = per_page_default
    paginator = Paginator(qs, per_page)
    page = request.GET.get("page") or 1
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    # Build querystring without 'page' for pagination links
    from urllib.parse import urlencode
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    base_querystring = ("?" + urlencode(query_params, doseq=True)) if query_params else ""

    context = {"orders": orders_page, "filter_form": form, "base_querystring": base_querystring, "per_page": per_page}
    return render(request, "orders/list.html", context)


@login_required
def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_activity(request, ActivityLog.CREATE, instance=obj)
            return redirect(reverse("orders_list"))
    else:
        form = OrderForm()
    return render(request, "orders/form.html", {"form": form})


@login_required
def order_edit(request, pk: int):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            obj = form.save()
            log_activity(request, ActivityLog.UPDATE, instance=obj)
            return redirect(reverse("orders_list"))
    else:
        form = OrderForm(instance=order)
    return render(request, "orders/form.html", {"form": form, "object": order})


@login_required
def order_delete(request, pk: int):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        log_activity(request, ActivityLog.DELETE, instance=order)
        order.delete()
        return redirect(reverse("orders_list"))
    return render(request, "orders/confirm_delete.html", {"object": order})


@login_required
def partners_list(request):
    partners = Partner.objects.all()
    return render(request, "partners/list.html", {"partners": partners})


@login_required
def logs_list(request):
    logs = ActivityLog.objects.select_related("user").all()
    return render(request, "logs/list.html", {"logs": logs})


@login_required
def partner_create(request):
    if request.method == "POST":
        form = PartnerForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_activity(request, ActivityLog.CREATE, instance=obj)
            return redirect(reverse("partners_list"))
    else:
        form = PartnerForm()
    return render(request, "partners/form.html", {"form": form})


@login_required
def partner_edit(request, pk: int):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            obj = form.save()
            log_activity(request, ActivityLog.UPDATE, instance=obj)
            return redirect(reverse("partners_list"))
    else:
        form = PartnerForm(instance=partner)
    return render(request, "partners/form.html", {"form": form, "object": partner})


@login_required
def partner_delete(request, pk: int):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        log_activity(request, ActivityLog.DELETE, instance=partner)
        partner.delete()
        return redirect(reverse("partners_list"))
    return render(request, "partners/confirm_delete.html", {"object": partner})

class LoginForm(django_forms.Form):
    username = django_forms.CharField(widget=django_forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم المستخدم"}))
    password = django_forms.CharField(widget=django_forms.PasswordInput(attrs={"class": "form-control", "placeholder": "كلمة المرور"}))


def login_view(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard"))
    form = LoginForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or reverse("dashboard")
            return redirect(next_url)
        else:
            error = "بيانات الدخول غير صحيحة"
    return render(request, "auth/login.html", {"form": form, "error": error})


@login_required
def logout_view(request):
    logout(request)
    return redirect(reverse("login"))
