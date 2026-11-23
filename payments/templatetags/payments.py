"""
Custom template tags for the payments app.
"""

from django import template

register = template.Library()


@register.filter
def format_price(amount, currency="NGN"):
    """
    Format a price with currency symbol.

    Usage:
        {{ amount|format_price }}
        {{ amount|format_price:"USD" }}
    """
    if amount is None:
        return "—"

    try:
        value = float(amount)
    except (TypeError, ValueError):
        return str(amount)

    symbols = {
        "NGN": "₦",
        "USD": "$",
        "GBP": "£",
        "EUR": "€",
    }

    symbol = symbols.get(str(currency).upper(), "")

    # 5000 -> ₦5,000.00 ; 5000.5 -> ₦5,000.50
    if value == int(value):
        return f"{symbol}{int(value):,}"

    return f"{symbol}{value:,.2f}"


@register.filter
def gateway_label(gateway):
    """
    Human-readable gateway name.

    Usage:
        {{ purchase.gateway|gateway_label }}
    """
    labels = {
        "paystack": "Paystack",
        "stripe": "Stripe",
    }

    return labels.get(str(gateway).lower(), str(gateway).title())


@register.filter
def content_type_label(content_type):
    """
    Human-readable content type label.

    Usage:
        {{ purchase.content_type|content_type_label }}
    """
    labels = {
        "subject": "Subject",
        "school_class": "School Class",
        "exam": "Examination",
        "exam_resource": "Exam Resource",
        "tech_course": "Tech Course",
        "tech_module": "Tech Module",
    }

    return labels.get(str(content_type).lower(), str(content_type).title())