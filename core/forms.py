from django import forms
from .models import Order, Partner


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["name", "order_type", "price", "date", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم الطلب"}),
            "order_type": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "1", "placeholder": "0"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "وصف اختياري"}),
        }


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ["name", "joined_amount", "percentage"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم الشريك"}),
            "joined_amount": forms.NumberInput(attrs={"class": "form-control", "step": "1", "placeholder": "0"}),
            "percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0-100"}),
        }

    def clean_percentage(self):
        percentage = self.cleaned_data.get("percentage")
        if percentage is None:
            return percentage
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError("Percentage must be between 0 and 100.")
        return percentage


class OrderFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "بحث بالاسم أو الوصف",
    }))
    order_type = forms.ChoiceField(required=False, choices=[("", "الكل")] + Order.TYPE_CHOICES, widget=forms.Select(attrs={
        "class": "form-select",
    }))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
    }))
    price_min = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        "class": "form-control",
        "step": "1",
        "placeholder": "Min",
    }))
    price_max = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        "class": "form-control",
        "step": "1",
        "placeholder": "Max",
    }))
    sort_by = forms.ChoiceField(required=False, choices=[
        ("-date", "الأحدث أولاً"),
        ("date", "الأقدم أولاً"),
        ("-price", "الأعلى سعراً"),
        ("price", "الأقل سعراً"),
        ("name", "الاسم تصاعدي"),
        ("-name", "الاسم تنازلي"),
    ], widget=forms.Select(attrs={
        "class": "form-select",
    }))

    per_page = forms.ChoiceField(required=False, choices=[
        ("10", "10"),
        ("25", "25"),
        ("50", "50"),
        ("100", "100"),
    ], initial="10", widget=forms.Select(attrs={
        "class": "form-select",
    }))


class DashboardFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
    }))

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
        return cleaned_data
