"""Shopping cart pricing (synthetic trial app for the North Star hosted CI trial)."""


def subtotal(items):
    return round(sum(i["price"] * i["qty"] for i in items), 2)
