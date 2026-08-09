from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from store.models import Product, Category, Banner
from store.forms import ProductForm, CategoryForm, BannerForm


# ─── AUTH ────────────────────────────────────────────────────────────────────

# Allowed hardcoded admin accounts
# ─── AUTH ────────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    error = 'This account has been disabled. Please contact support.'
                elif not user.is_staff:
                    error = 'You do not have admin access. Contact the store owner.'
                else:
                    login(request, user)
                    next_url = request.GET.get('next', '')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('admin_dashboard')
            else:
                error = 'Incorrect username or password. Please try again.'

    return render(request, 'admin_panel/login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def dashboard(request):
    if not request.user.is_staff:
        logout(request)
        return redirect('admin_login')
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(in_stock=True).count()
    out_of_stock = Product.objects.filter(in_stock=False).count()
    flash_sale_count = Product.objects.filter(is_flash_sale=True).count()
    featured_count = Product.objects.filter(is_featured=True).count()
    total_categories = Category.objects.count()
    total_banners = Banner.objects.count()
    active_banners = Banner.objects.filter(is_active=True).count()
    recent_products = Product.objects.order_by('-created_at')[:6]

    smartphones_count = Product.objects.filter(category='smartphones').count()
    accessories_count = Product.objects.filter(category='accessories').count()
    smartwatch_count = Product.objects.filter(category='smart-watches').count()
    audio_count = Product.objects.filter(category='audio-gadgets').count()

    context = {
        'total_products': total_products,
        'in_stock': in_stock,
        'out_of_stock': out_of_stock,
        'flash_sale_count': flash_sale_count,
        'featured_count': featured_count,
        'total_categories': total_categories,
        'total_banners': total_banners,
        'active_banners': active_banners,
        'recent_products': recent_products,
        'smartphones_count': smartphones_count,
        'accessories_count': accessories_count,
        'smartwatch_count': smartwatch_count,
        'audio_count': audio_count,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def product_list(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    stock = request.GET.get('stock', '')
    products = Product.objects.all().order_by('-created_at')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if cat:
        products = products.filter(category=cat)
    if stock == 'in':
        products = products.filter(in_stock=True)
    elif stock == 'out':
        products = products.filter(in_stock=False)
    categories = Category.objects.all().order_by('order')
    context = {'products': products, 'q': q, 'cat': cat, 'stock': stock, 'categories': categories}
    return render(request, 'admin_panel/products/list.html', context)


@login_required(login_url='admin_login')
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if request.FILES.get('image_file'):
                product.image_url = save_uploaded_image(request.FILES['image_file'], 'products')
            if request.FILES.get('image2_file'):
                product.image2_url = save_uploaded_image(request.FILES['image2_file'], 'products')
            product.save()
            messages.success(request, '✅ Product added successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'admin_panel/products/form.html', {'form': form, 'action': 'Add New Product'})


@login_required(login_url='admin_login')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if request.FILES.get('image_file'):
                product.image_url = save_uploaded_image(request.FILES['image_file'], 'products')
            if request.FILES.get('image2_file'):
                product.image2_url = save_uploaded_image(request.FILES['image2_file'], 'products')
            product.save()
            messages.success(request, '✅ Product updated successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/products/form.html', {'form': form, 'action': 'Edit Product', 'product': product})


@login_required(login_url='admin_login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, '🗑️ Watch deleted.')
    return redirect('admin_product_list')


@login_required(login_url='admin_login')
def product_toggle_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.in_stock = not product.in_stock
    product.save()
    return redirect('admin_product_list')


# ─── CATEGORIES ──────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'admin_panel/categories/list.html', {'categories': categories})


@login_required(login_url='admin_login')
def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Category added!')
            return redirect('admin_category_list')
    else:
        form = CategoryForm()
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'action': 'Add Category'})


@login_required(login_url='admin_login')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Category updated!')
            return redirect('admin_category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'action': 'Edit Category', 'category': category})


@login_required(login_url='admin_login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, '🗑️ Category deleted.')
    return redirect('admin_category_list')


# ─── BANNERS ─────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def banner_list(request):
    banners = Banner.objects.all().order_by('order')
    return render(request, 'admin_panel/banners/list.html', {'banners': banners})


@login_required(login_url='admin_login')
def banner_add(request):
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save(commit=False)
            if request.FILES.get('image_file'):
                banner.image_url = save_uploaded_image(request.FILES['image_file'], 'banners')
            banner.save()
            messages.success(request, '✅ Banner added!')
            return redirect('admin_banner_list')
    else:
        form = BannerForm()
    return render(request, 'admin_panel/banners/form.html', {'form': form, 'action': 'Add Banner'})


@login_required(login_url='admin_login')
def banner_edit(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        form = BannerForm(request.POST, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Banner updated!')
            return redirect('admin_banner_list')
    else:
        form = BannerForm(instance=banner)
    return render(request, 'admin_panel/banners/form.html', {'form': form, 'action': 'Edit Banner', 'banner': banner})


@login_required(login_url='admin_login')
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        banner.delete()
        messages.success(request, '🗑️ Banner deleted.')
    return redirect('admin_banner_list')


@login_required(login_url='admin_login')
def banner_toggle(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.is_active = not banner.is_active
    banner.save()
    messages.success(request, f'Banner {"activated" if banner.is_active else "deactivated"}.')
    return redirect('admin_banner_list')


# ─── ORDERS ──────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def order_list(request):
    if not request.user.is_staff:
        logout(request)
        return redirect('admin_login')

    from accounts.models import Order
    orders = Order.objects.all().select_related('user')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'admin_panel/orders/list.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required(login_url='admin_login')
def order_detail(request, pk):
    if not request.user.is_staff:
        logout(request)
        return redirect('admin_login')

    from accounts.models import Order
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [c[0] for c in Order.STATUS_CHOICES]:
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated to "{order.get_status_display()}".')
            return redirect('admin_order_detail', pk=order.pk)

    return render(request, 'admin_panel/orders/detail.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })


# ─── SITE SETTINGS (COMPANY EMAIL) ────────────────────────────────────────────

@login_required(login_url='admin_login')
def site_settings(request):
    if not request.user.is_staff:
        logout(request)
        return redirect('admin_login')

    from store.models import SiteSettings
    from django.utils.dateparse import parse_datetime
    setting_obj = SiteSettings.objects.first()

    if request.method == 'POST':
        email = request.POST.get('company_email', '').strip()
        phone = request.POST.get('company_phone', '').strip()
        email_password = request.POST.get('email_password', '').strip()
        sale_end_str = request.POST.get('flash_sale_end_time', '').strip()
        action = request.POST.get('action', '')

        if action == 'delete' and setting_obj:
            setting_obj.delete()
            messages.success(request, '🗑️ Settings deleted.')
            return redirect('admin_site_settings')

        sale_end_dt = parse_datetime(sale_end_str) if sale_end_str else None

        if setting_obj:
            setting_obj.company_email = email if email else setting_obj.company_email
            setting_obj.company_phone = phone if phone else setting_obj.company_phone
            setting_obj.email_password = email_password
            setting_obj.flash_sale_end_time = sale_end_dt
            setting_obj.save()
            messages.success(request, '✅ Site Settings, Phone Number & Flash Sale Timer updated successfully!')
        else:
            SiteSettings.objects.create(company_email=email, company_phone=phone, email_password=email_password, flash_sale_end_time=sale_end_dt)
            messages.success(request, '✅ Site Settings, Phone Number & Flash Sale Timer saved successfully!')
            
        return redirect('admin_site_settings')

    return render(request, 'admin_panel/settings.html', {'setting': setting_obj})
