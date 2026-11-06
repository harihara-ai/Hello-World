"""Shopping cart pricing."""


def subtotal(items):
    return round(sum(i["price"] * i["qty"] for i in items), 2)


def bulk_discount(items):
    """REQ-CART-001, REQ-CART-002: 5 percent off when 10 or more units are bought."""
    if any(i["qty"] < 0 for i in items):
        raise ValueError("negative quantity")
    units = sum(i["qty"] for i in items)
    return round(subtotal(items) * 0.05, 2) if units >= 10 else 0.0
