from django.contrib import admin
from .models import Feedback, FeedbackImage


class FeedbackImageInline(admin.TabularInline):
    model = FeedbackImage
    extra = 0
    readonly_fields = ('image',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buyer_name', 'product__name', 'comment')
    readonly_fields = ('created_at',)
    inlines = [FeedbackImageInline]
