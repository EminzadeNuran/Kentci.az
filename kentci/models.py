from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------
# Base Model və Soft Delete
# -------------------------
class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated")
    is_deleted = models.BooleanField(default=False)

    objects = BaseModelManager()
    all_objects = models.Manager()  # includes deleted

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

# -------------------------
# User Model
# -------------------------
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MODERATOR = 'moderator', 'Moderator'
        CUSTOMER = 'customer', 'Customer'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=15, blank=True, null=True, validators=[RegexValidator(r'^\+?\d{9,15}$')])
    profile_picture = models.ImageField(upload_to='users/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    loyalty_points = models.PositiveIntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

# -------------------------
# Admin Audit Log
# -------------------------
class AdminAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Audit Log"
        verbose_name_plural = "Admin Audit Logs"
        ordering = ['-created_at']

# -------------------------
# Category Model (Multi-language)
# -------------------------
class Category(BaseModel):
    name = models.JSONField(default=dict)
    description = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name.get("en", "Category")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['created_at']

# -------------------------
# Product Model
# -------------------------
class Product(BaseModel):
    name = models.JSONField(default=dict)
    description = models.JSONField(default=dict, blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    images = ArrayField(models.CharField(max_length=255), blank=True, default=list)
    videos = ArrayField(models.CharField(max_length=255), blank=True, default=list)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default='USD')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.get("en", "product"))
        super().save(*args, **kwargs)

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'Out of stock'
        elif self.quantity < 5:
            return 'Low stock'
        return 'In stock'

    @property
    def is_available(self):
        return self.is_active and self.quantity > 0

    def __str__(self):
        return self.name.get("en", "Product")

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['created_at']

# -------------------------
# Product Stock History
# -------------------------
class ProductStockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    quantity_change = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Product Stock History"
        verbose_name_plural = "Product Stock Histories"
        ordering = ['-created_at']

# -------------------------
# Coupon Model
# -------------------------
class Coupon(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    name = models.JSONField(default=dict, blank=True)

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def apply_discount(self, total_amount):
        if self.is_valid():
            return total_amount * (1 - self.discount_percent / 100)
        return total_amount

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ['-valid_from']

# -------------------------
# Wishlist
# -------------------------
class WishlistItem(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    notify_when_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} → {self.product.name.get('en','Product')}"

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

# -------------------------
# Order Model
# -------------------------
class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_date = models.DateTimeField(null=True, blank=True)

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        total = sum(item.get_total_price for item in self.items.all()) + self.shipping_cost
        if self.coupon:
            total = self.coupon.apply_discount(total)
        return total

    @property
    def is_paid(self):
        return hasattr(self, 'payment') and self.payment.status == Payment.Status.COMPLETED

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

# -------------------------
# Order Item
# -------------------------
class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    @property
    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name.get('en','Product')}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['id']

# -------------------------
# Cart Item
# -------------------------
class CartItem(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.quantity * self.product.price

    @property
    def is_available(self):
        return self.product.quantity >= self.quantity

    def save(self, *args, **kwargs):
        if self.quantity > self.product.quantity:
            self.quantity = self.product.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name.get('en','Product')} ({self.user.username})"

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

# -------------------------
# Review
# -------------------------
class Review(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"{self.user.username} - {self.product.name.get('en','Product')} ({self.rating})"

# -------------------------
# Payment Model
# -------------------------
class Payment(BaseModel):
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        ONLINE = 'online', 'Online'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    webhook_status = models.CharField(max_length=50, blank=True, null=True)
    webhook_payload = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} ({self.status})"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-paid_at']

# -------------------------
# Webhook Log
# -------------------------
class WebhookLog(models.Model):
    url = models.URLField()
    payload = models.JSONField()
    response_status = models.IntegerField(blank=True, null=True)
    response_body = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Webhook Log"
        verbose_name_plural = "Webhook Logs"
        ordering = ['-created_at']

# -------------------------
# Signals
# -------------------------
@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    reviews = instance.product.reviews.filter(approved=True)
    instance.product.review_count = reviews.count()
    instance.product.rating_average = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    instance.product.save()

@receiver(post_save, sender=Payment)
def update_order_status(sender, instance, **kwargs):
    if instance.status == Payment.Status.COMPLETED:
        instance.order.status = Order.Status.COMPLETED
        instance.order.save()
