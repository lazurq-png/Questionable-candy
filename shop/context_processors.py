"""Template context available on every page."""
from . import cart


def shoppingcart(request):
    """The item count behind the header's cart link (UC-04 step 3)."""
    return {"shoppingcart_count": cart.count(request)}
