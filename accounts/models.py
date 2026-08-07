import uuid
from django.db import models
from django.contrib.auth.models import User
from store.models import Product


class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    password = models.CharField(max_length=250)  # hashed or plain temp
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OTP for {self.email}: {self.code}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.user.email}"

    @property
    def initials(self):
        first = self.user.first_name[:1].upper() if self.user.first_name else ''
        last = self.user.last_name[:1].upper() if self.user.last_name else ''
        return (first + last) or self.user.username[:2].upper()


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} — {self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.product.sale_price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('card', 'Credit / Debit Card'),
        ('bank', 'Bank Transfer'),
        ('jazzcash', 'JazzCash'),
        ('easypaisa', 'EasyPaisa'),
    ]
    # Nullable for guest orders
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Unique token for guest order tracking link
    tracking_token = models.UUIDField(default=uuid.uuid4, editable=False)

    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')

    # Delivery address (structured)
    house_number  = models.CharField(max_length=100, blank=True)
    street_colony = models.CharField(max_length=300, blank=True)
    city          = models.CharField(max_length=100, blank=True)
    landmark      = models.CharField(max_length=300, blank=True)

    # Map pin coordinates (Leaflet)
    map_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    map_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Guest customer info (blank for logged-in orders)
    guest_name  = models.CharField(max_length=200, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        customer = self.user.username if self.user else self.guest_name
        return f"Order #{self.id} — {customer} — {self.status}"

    @property
    def customer_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name

    @property
    def customer_email(self):
        return self.user.email if self.user else self.guest_email

    @property
    def customer_phone(self):
        if self.user:
            try:
                return self.user.profile.phone
            except Exception:
                return ''
        return self.guest_phone

    @property
    def full_address(self):
        parts = [self.house_number, self.street_colony, self.city]
        if self.landmark:
            parts.append(f"Near: {self.landmark}")
        return ', '.join(p for p in parts if p)

    @property
    def maps_link(self):
        if self.map_lat and self.map_lng:
            return f"https://maps.google.com/?q={self.map_lat},{self.map_lng}"
        return None

    @property
    def is_guest(self):
        return self.user is None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.price_at_purchase * self.quantity
