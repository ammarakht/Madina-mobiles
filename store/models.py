from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, blank=True)  # emoji or icon class
    image_url = models.CharField(max_length=500, blank=True)
    subtitle = models.CharField(max_length=100, blank=True)  # e.g. "NEW COLLECTION"
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Categories'

    @property
    def is_new(self):
        """Returns True if category was created within the last 30 days (1 month)."""
        if self.created_at:
            return (timezone.now() - self.created_at).days <= 30
        return False

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('smartphones', 'Smartphones'),
        ('accessories', 'Accessories'),
        ('smart-watches', 'Smart Watches'),
        ('audio-gadgets', 'Audio & Gadgets'),
    ]
    name = models.CharField(max_length=300)
    sku = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='smartphones')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    review_count = models.IntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    is_flash_sale = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    image_url = models.CharField(max_length=500, blank=True)
    image2_url = models.CharField(max_length=500, blank=True)  # hover image
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def discount_percent(self):
        if self.original_price > 0:
            discount = ((self.original_price - self.sale_price) / self.original_price) * 100
            return int(discount)
        return 0

    def __str__(self):
        return self.name


class Banner(models.Model):
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True)
    cta_text = models.CharField(max_length=100, default='Shop Now')
    cta_link = models.CharField(max_length=200, default='#')
    image_url = models.CharField(max_length=500, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class SearchLog(models.Model):
    """Tracks search queries performed by users"""
    from django.contrib.auth.models import User
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=300)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else 'Guest'
        return f"{user_str}: '{self.query}' at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class ProductView(models.Model):
    """Tracks product views/clicks"""
    from django.contrib.auth.models import User
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else 'Guest'
        return f"{user_str} viewed {self.product.name}"


class SiteSettings(models.Model):
    """
    Global site configuration. Only ONE record should exist at a time.
    Used by admin portal to set company email, phone number, and flash sale timer.
    """
    company_email = models.EmailField(blank=True, null=True)
    company_phone = models.CharField(max_length=50, blank=True, null=True, default='03407608138')
    email_password = models.CharField(max_length=200, blank=True, null=True)
    flash_sale_end_time = models.DateTimeField(blank=True, null=True)
    label = models.CharField(max_length=100, default='Site Settings', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return f"Site Settings ({self.company_email} / {self.company_phone})"

    @classmethod
    def get_email(cls):
        """Returns the configured company email, or None if not set."""
        obj = cls.objects.first()
        return obj.company_email if obj else None

    @classmethod
    def get_phone(cls):
        """Returns the configured company phone, or default."""
        obj = cls.objects.first()
        if obj and obj.company_phone:
            return obj.company_phone
        return '03407608138'

    @classmethod
    def get_whatsapp_phone(cls):
        """Returns formatted international digits for wa.me link e.g. 923407608138."""
        phone = cls.get_phone()
        digits = ''.join(filter(str.isdigit, phone))
        if digits.startswith('0'):
            digits = '92' + digits[1:]
        elif not digits.startswith('92'):
            digits = '92' + digits
        return digits

    @classmethod
    def get_flash_sale_end(cls):
        """Returns flash sale end datetime, or None."""
        obj = cls.objects.first()
        return obj.flash_sale_end_time if obj else None


class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feedbacks')
    order_item = models.OneToOneField('accounts.OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    buyer_name = models.CharField(max_length=200)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer_name} - {self.product.name} ({self.rating} stars)"


class FeedbackImage(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='feedback_pics/')

    def __str__(self):
        return f"Image for Feedback #{self.feedback.id}"


