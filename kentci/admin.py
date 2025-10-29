from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

# -------------------------
# Inline Classes (əlaqəli modellər üçün)
# -------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1

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
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')


# -------------------------
# User Admin
# -------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        (_('Role'), {'fields': ('role',)}),
    )


# -------------------------
# Product Admin
# -------------------------
@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ('id', 'get_name', 'category', 'price', 'rating_average', 'quantity', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name__en', 'name__az', 'name__ru', 'slug')
    inlines = [ProductImageInline, ProductVideoInline, ReviewInline]

    def get_name(self, obj):
        return obj.name.get('en', '—')
    get_name.short_description = 'Name (EN)'


# -------------------------
# Category Admin
# -------------------------
@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ('id', 'get_name', 'parent', 'slug', 'is_active')
    search_fields = ('name__en', 'name__az', 'name__ru', 'slug')

    def get_name(self, obj):
        return obj.name.get('en', '—')
    get_name.short_description = 'Name (EN)'


# -------------------------
# Order Admin
# -------------------------
@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = ('id', 'user', 'status', 'final_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    inlines = [OrderItemInline]


# -------------------------
# Payment Admin
# -------------------------
@admin.register(Payment)
class PaymentAdmin(BaseAdmin):
    list_display = ('id', 'order', 'method', 'status', 'amount', 'last_attempt')
    list_filter = ('status', 'method')
    search_fields = ('order__user__username',)


# -------------------------
# Coupon Admin
# -------------------------
@admin.register(Coupon)
class CouponAdmin(BaseAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'expires_at')
    list_filter = ('is_active',)
    search_fields = ('code',)


# -------------------------
# Review Admin
# -------------------------
@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ('id', 'product', 'user', 'rating', 'is_verified_purchase', 'approved', 'created_at')
    list_filter = ('approved', 'is_verified_purchase', 'rating')
    search_fields = ('product__name__en', 'user__username')


# -------------------------
# Log və Tarixçələr
# -------------------------
@admin.register(ProductStockHistory)
class ProductStockHistoryAdmin(BaseAdmin):
    list_display = ('product', 'change', 'reason', 'created_at')
    list_filter = ('reason',)
    search_fields = ('product__name__en',)


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(BaseAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'created_at')
    list_filter = ('model_name', 'action')


@admin.register(WebhookLog)
class WebhookLogAdmin(BaseAdmin):
    list_display = ('event_type', 'status', 'response_time', 'created_at')
    list_filter = ('status', 'event_type')
