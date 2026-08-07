from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.customer_register, name='customer_register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.customer_login, name='customer_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('profile/', views.customer_profile, name='customer_profile'),
    path('orders/', views.my_orders, name='my_orders'),
    path('api/cart/sync/', views.sync_cart, name='sync_cart'),
]
