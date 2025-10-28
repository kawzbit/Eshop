from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    """Shopping cart handler using Django session storage."""
    
    def __init__(self, request):
        self.session = request.session
        self.cart = self._get_or_create_cart()
    
    def _get_or_create_cart(self):
        """Retrieve existing cart or create new empty cart in session."""
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = {}
            self.session[settings.CART_SESSION_ID] = cart
        return cart
    
    def add(self, product: Product, quantity: int = 1, override_quantity: bool = False):
        """
        Add product to cart or update quantity.
        
        Args:
            product: Product instance to add
            quantity: Number of items to add
            override_quantity: If True, replace quantity instead of adding
        """
        product_id = str(product.id)
        
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        self.cart[product_id]['quantity'] = quantity if override_quantity else \
            self.cart[product_id]['quantity'] + quantity
        
        self.save()
    
    def remove(self, product):
        """Remove product from cart if it exists."""
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart.pop(product_id)
            self.save()
    
    def save(self):
        """Mark session as modified to ensure persistence."""
        self.session.modified = True
    
    def clear(self):
        """Empty the cart by removing it from session."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()
    
    def get_total_price(self):
        """Calculate total price for all items in cart."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )
    
    def __iter__(self):
        """
        Iterate cart items with product objects attached.
        Yields enriched cart items with product, price, and total_price.
        """
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        
        # Create lookup dictionary for efficient product retrieval
        product_lookup = {str(p.id): p for p in products}
        
        for product_id, item in self.cart.items():
            if product_id in product_lookup:
                enriched_item = item.copy()
                enriched_item['product'] = product_lookup[product_id]
                enriched_item['price'] = Decimal(item['price'])
                enriched_item['total_price'] = enriched_item['price'] * item['quantity']
                yield enriched_item
    
    def __len__(self):
        """Return total quantity of all items in cart."""
        return sum(item['quantity'] for item in self.cart.values())

