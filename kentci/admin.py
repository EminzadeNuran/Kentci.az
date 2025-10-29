from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Product, Category, Order, OrderItem, Payment, Coupon, Review,
    ProductStockHistory, AdminAuditLog, WebhookLog
)

# -------------------------
# Inline Classes
# -------------------------
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('created_at',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# -------------------------
# Base Admin
# -------------------------
class BaseAdmin(admin.ModelAdmin):
    list_per_page = 20
    readonly_fields = ('created_at',)

# -------------------------
# User Admin
# -------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone', 'profile_picture', 'bio')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        (_('Role'), {'fields': ('role',)}),
    )

# -------------------------
# Product Admin
# -------------------------
@admin.register(Product)
class ProductAdmin(BaseAdmin):
    readonly_fields = ('created_at', 'updated_at')  # BaseModel sahələri
    list_display = ('id', 'get_name', 'category', 'price', 'rating_average', 'quantity', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name__en', 'name__az', 'name__ru', 'slug')
    inlines = [ReviewInline]

    @admin.display(description='Name (EN)')
    def get_name(self, obj):
        return obj.name.get('en', '—')

# -------------------------
# Category Admin
# -------------------------
@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ('id', 'get_name')
    search_fields = ('name__en', 'name__az', 'name__ru')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Name (EN)')
    def get_name(self, obj):
        return obj.name.get('en', '—')

# -------------------------
# Order Admin
# -------------------------
@admin.register(Order)
class OrderAdmin(BaseAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'user', 'status', 'get_total_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email')
    inlines = [OrderItemInline]

    @admin.display(description='Total Price')
    def get_total_price(self, obj):
        return obj.total_price

# -------------------------
# Payment Admin
# -------------------------
@admin.register(Payment)
class PaymentAdmin(BaseAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'order', 'payment_method', 'status', 'amount', 'paid_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('order__user__username',)

# -------------------------
# Coupon Admin
# -------------------------
@admin.register(Coupon)
class CouponAdmin(BaseAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('code', 'discount_percent', 'active', 'valid_to')
    list_filter = ('active',)
    search_fields = ('code',)

# -------------------------
# Review Admin
# -------------------------
@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ('id', 'product', 'user', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'rating')
    search_fields = ('product__name__en', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

# -------------------------
# Product Stock History Admin
# -------------------------
@admin.register(ProductStockHistory)
class ProductStockHistoryAdmin(BaseAdmin):
    list_display = ('product', 'quantity_change', 'reason', 'created_at')
    list_filter = ('reason',)
    search_fields = ('product__name__en',)
    readonly_fields = ('created_at',)

# -------------------------
# Admin Audit Log Admin
# -------------------------
@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(BaseAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'created_at')
    list_filter = ('model_name', 'action')
    readonly_fields = ('created_at',)

# -------------------------
# Webhook Log Admin
# -------------------------
@admin.register(WebhookLog)
class WebhookLogAdmin(BaseAdmin):
    list_display = ('id', 'url', 'created_at')
    search_fields = ('url',)
    readonly_fields = ('created_at',)
