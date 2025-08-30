from django import template

register = template.Library()


@register.filter()
def iqd(value):
    """Format a numeric value as Iraqi Dinar (IQD)."""
    if value is None:
        return "IQD 0"
    try:
        # Format with thousands separator, no decimals
        amount = f"{float(value):,.0f}".replace(",", ",")
    except Exception:
        return f"IQD {value}"
    return f"IQD {amount}"


