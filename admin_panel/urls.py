from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # Dashboard
    path('', views.dashboard, name='admin_dashboard'),

    # Products
    path('watches/', views.product_list, name='admin_product_list'),
    path('watches/add/', views.product_add, name='admin_product_add'),
    path('watches/<int:pk>/edit/', views.product_edit, name='admin_product_edit'),
    path('watches/<int:pk>/delete/', views.product_delete, name='admin_product_delete'),
    path('watches/<int:pk>/toggle-stock/', views.product_toggle_stock, name='admin_product_toggle_stock'),

    # Categories
    path('categories/', views.category_list, name='admin_category_list'),
    path('categories/add/', views.category_add, name='admin_category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='admin_category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='admin_category_delete'),

    # Banners
    path('banners/', views.banner_list, name='admin_banner_list'),
    path('banners/add/', views.banner_add, name='admin_banner_add'),
    path('banners/<int:pk>/edit/', views.banner_edit, name='admin_banner_edit'),
    path('banners/<int:pk>/delete/', views.banner_delete, name='admin_banner_delete'),
    path('banners/<int:pk>/toggle/', views.banner_toggle, name='admin_banner_toggle'),

    # Orders Management
    path('orders/', views.order_list, name='admin_order_list'),
    path('orders/<int:pk>/', views.order_detail, name='admin_order_detail'),

    # Site Settings (Company Email Management)
    path('settings/', views.site_settings, name='admin_site_settings'),
]
