from .cart import Cart


def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart(request)
        return {'cart_item_count': len(cart)}
    return {'cart_item_count': 0}
