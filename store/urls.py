from django.urls import path
from . import views

from . import checkout_views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.category_products, {'category_slug': 'all'}, name='all_products'),
    path('category/<str:category_slug>/', views.category_products, name='category_products'),
    path('api/search/', views.search_products, name='search_products'),
    path('api/product/<int:product_id>/', views.product_detail_api, name='product_detail_api'),
    path('api/feedback/submit/', views.submit_feedback, name='submit_feedback'),
    
    # Checkout routes
    path('checkout/start/', checkout_views.checkout_start, name='checkout_start'),
    path('checkout/address/', checkout_views.checkout_address, name='checkout_address'),
    path('checkout/payment/', checkout_views.checkout_payment, name='checkout_payment'),
    path('checkout/confirm/<str:token>/', checkout_views.checkout_confirm, name='checkout_confirm'),
    
    # Guest order tracking
    path('track/<str:token>/', checkout_views.track_order, name='track_order'),
    path('track-order/', checkout_views.track_order_search, name='track_order_search'),
]
