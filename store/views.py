from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Banner, Category, SearchLog, ProductView, Feedback, FeedbackImage
from accounts.models import OrderItem
from django.views.decorators.http import require_POST
from django.contrib import messages
from .recommendations import get_customer_recommendations


def search_products(request):
    query = request.GET.get('q', '').strip()
    results = []
    if len(query) >= 2:
        # Log search query for recommendations
        user = request.user if request.user.is_authenticated else None
        SearchLog.objects.create(user=user, query=query)

        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query),
            in_stock=True
        )[:8]
        for p in products:
            results.append({
                'id': p.id,
                'name': p.name,
                'sale_price': float(p.sale_price),
                'original_price': float(p.original_price),
                'image_url': p.image_url,
                'discount_percent': p.discount_percent,
            })
    return JsonResponse({'results': results})


def product_detail_api(request, product_id):
    """Returns full product details as JSON for the quick-view popup modal."""
    try:
        p = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    # Build image gallery — include all non-empty image fields
    images = []
    if p.image_url:
        images.append(p.image_url)
    if p.image2_url:
        images.append(p.image2_url)

    # Log the product view for recommendations
    user = request.user if request.user.is_authenticated else None
    ProductView.objects.create(user=user, product=p)

    category_labels = dict(Product.CATEGORY_CHOICES)

    feedbacks_data = []
    feedbacks = p.feedbacks.all().order_by('-created_at')
    for f in feedbacks:
        feedbacks_data.append({
            'buyer_name': f.buyer_name,
            'rating': f.rating,
            'comment': f.comment,
            'created_at': f.created_at.strftime('%B %d, %Y'),
            'images': [img.image.url for img in f.images.all()]
        })

    return JsonResponse({
        'id': p.id,
        'name': p.name,
        'sku': p.sku or f'SKU-{p.id:04d}',
        'category': category_labels.get(p.category, p.category),
        'category_slug': p.category,
        'original_price': float(p.original_price),
        'sale_price': float(p.sale_price),
        'discount_percent': p.discount_percent,
        'rating': float(p.rating),
        'review_count': p.review_count,
        'in_stock': p.in_stock,
        'is_flash_sale': p.is_flash_sale,
        'is_featured': p.is_featured,
        'images': images,
        'feedbacks': feedbacks_data,
    })



def home(request):

    # Load active banners from database
    db_banners = Banner.objects.filter(is_active=True).order_by('order')
    hero_slides = []
    for banner in db_banners:
        target_link = banner.cta_link
        if not target_link or target_link == '#':
            sub_lower = banner.subtitle.lower()
            if 'iphone' in sub_lower or 'smartphone' in sub_lower:
                target_link = '/category/smartphones/'
            elif 'accessories' in sub_lower or 'protect' in sub_lower:
                target_link = '/category/accessories/'
            elif 'watch' in sub_lower:
                target_link = '/category/smart-watches/'
            else:
                target_link = '/category/all/'

        hero_slides.append({
            'title': banner.title,
            'highlight': banner.subtitle.split(' — ')[0] if ' — ' in banner.subtitle else banner.title,
            'subtitle': banner.subtitle.split(' — ')[1] if ' — ' in banner.subtitle else banner.subtitle,
            'cta': banner.cta_text,
            'link': target_link,
            'image': banner.image_url,
        })

    # Fallback to static slides if no banners exist
    if not hero_slides:
        hero_slides = [
            {
                'title': 'Introducing',
                'highlight': 'iPhone 15 Pro Max',
                'subtitle': 'Titanium Design — The Ultimate iPhone',
                'cta': 'Shop Now',
                'image': 'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=1400&h=700&fit=crop&q=80',
            }
        ]

    # Load categories from DB
    db_categories = Category.objects.all().order_by('order')
    # Since categories map to circular navigation on top, let's map them
    categories_images = {
        'Smartphones': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&h=200&fit=crop',
        'Accessories': 'https://images.unsplash.com/photo-1608156639585-b3a032ef9689?w=200&h=200&fit=crop',
        'Smart Watches': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=200&h=200&fit=crop',
        'Audio & Gadgets': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200&h=200&fit=crop',
    }
    categories = []
    for cat in db_categories:
        categories.append({
            'name': cat.name,
            'slug': cat.slug,
            'sub': 'NEW COLLECTION' if 'Smart' in cat.name else '',
            'icon': cat.icon,
            'image': categories_images.get(cat.name, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&h=200&fit=crop'),
        })

    # Fallback categories if empty
    if not categories:
        categories = [
            {'name': 'Smartphones', 'slug': 'smartphones', 'sub': 'LATEST MODELS', 'icon': '📱', 'image': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&h=200&fit=crop'},
            {'name': 'Accessories', 'slug': 'accessories', 'sub': 'PREMIUM QUALITY', 'icon': '🔌', 'image': 'https://images.unsplash.com/photo-1608156639585-b3a032ef9689?w=200&h=200&fit=crop'},
            {'name': 'Smart Watches', 'slug': 'smart-watches', 'sub': 'ON THE WRIST', 'icon': '⌚', 'image': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=200&h=200&fit=crop'},
        ]

    # Load dynamic products
    flash_sale_products = Product.objects.filter(is_flash_sale=True, in_stock=True)[:4]
    men_products = Product.objects.filter(category='smartphones', in_stock=True)[:4]
    women_products = Product.objects.filter(category='accessories', in_stock=True)[:4]
    couples_products = Product.objects.filter(category='audio-gadgets', in_stock=True)[:4]
    smart_products = Product.objects.filter(category='smart-watches', in_stock=True)[:4]

    # Recommendations: Only computed if logged in (user explicitly requested to hide until login)
    recommended_products = []
    if request.user.is_authenticated and not request.user.is_staff:
        recommended_products = get_customer_recommendations(request.user, limit=4)

    context = {
        'hero_slides': hero_slides,
        'categories': categories,
        'flash_sale_products': flash_sale_products,
        'men_products': men_products,
        'women_products': women_products,
        'couples_products': couples_products,
        'smart_products': smart_products,
        'recommended_products': recommended_products,
    }
    return render(request, 'store/index.html', context)


def category_products(request, category_slug='all'):
    category_slug = category_slug.lower().strip()
    
    # Base queryset
    products = Product.objects.filter(in_stock=True)
    
    # Category metadata mapping
    category_info = {
        'smartphones': {
            'title': 'Smartphones',
            'subtitle': 'Discover the latest flagship & mid-range smartphones from Apple, Samsung, Xiaomi, OnePlus, Google & more.',
            'icon': '📱',
            'filter_cat': 'smartphones',
            'slug': 'smartphones'
        },
        'accessories': {
            'title': 'Mobile Accessories',
            'subtitle': 'Protect and power your devices with premium cases, fast chargers, tempered glass & power banks.',
            'icon': '🔌',
            'filter_cat': 'accessories',
            'slug': 'accessories'
        },
        'audio-gadgets': {
            'title': 'Audio & Gadgets',
            'subtitle': 'Experience superior sound with wireless earbuds, Bluetooth speakers & smart gadgets.',
            'icon': '🎧',
            'filter_cat': 'audio-gadgets',
            'slug': 'audio-gadgets'
        },
        'gadgets': {
            'title': 'Audio & Gadgets',
            'subtitle': 'Experience superior sound with wireless earbuds, Bluetooth speakers & smart gadgets.',
            'icon': '🎧',
            'filter_cat': 'audio-gadgets',
            'slug': 'audio-gadgets'
        },
        'smart-watches': {
            'title': 'Smart Watches',
            'subtitle': 'Stay connected, track your fitness, and monitor your health on the go.',
            'icon': '⌚',
            'filter_cat': 'smart-watches',
            'slug': 'smart-watches'
        },
        'watches': {
            'title': 'Smart Watches',
            'subtitle': 'Stay connected, track your fitness, and monitor your health on the go.',
            'icon': '⌚',
            'filter_cat': 'smart-watches',
            'slug': 'smart-watches'
        },
        'flash-sale': {
            'title': 'Flash Sale Items',
            'subtitle': 'Unbeatable limited-time discounts on top mobile phones and accessories.',
            'icon': '⚡',
            'flash_sale': True,
            'slug': 'flash-sale'
        },
        'sale': {
            'title': 'Special Sale & Offers',
            'subtitle': 'Unbeatable discount offers on premium smartphones, smartwatches, and accessories.',
            'icon': '🏷️',
            'on_sale': True,
            'slug': 'sale'
        },
        'best-sellers': {
            'title': 'Best Sellers',
            'subtitle': 'Our most popular and top-rated smartphones and accessories.',
            'icon': '⭐',
            'featured': True,
            'slug': 'best-sellers'
        },
        'all': {
            'title': 'All Products',
            'subtitle': 'Browse our complete catalog of smartphones, mobile accessories, smartwatches & gadgets.',
            'icon': '🛍️',
            'slug': 'all'
        }
    }
    
    info = category_info.get(category_slug, category_info['all'])
    
    if 'filter_cat' in info:
        products = products.filter(category=info['filter_cat'])
    elif info.get('flash_sale'):
        products = products.filter(is_flash_sale=True)
    elif info.get('featured'):
        products = products.filter(is_featured=True)
    elif info.get('on_sale'):
        from django.db.models import F
        products = products.filter(original_price__gt=F('sale_price'))
        
    # Optional search / brand filter from query string ?q=iphone
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        
    # Sorting
    sort = request.GET.get('sort', 'default')
    if sort == 'price_low':
        products = products.order_by('sale_price')
    elif sort == 'price_high':
        products = products.order_by('-sale_price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    else:
        products = products.order_by('-created_at')

    context = {
        'category_slug': category_slug,
        'info': info,
        'products': products,
        'total_count': products.count(),
        'sort': sort,
        'q': q,
    }
    return render(request, 'store/category.html', context)


@require_POST
def submit_feedback(request):
    """
    Submits user or guest feedback for a specific product inside an order.
    Accepts: order_item_id, rating, comment, and optional image files.
    """
    order_item_id = request.POST.get('order_item_id')
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    
    if not order_item_id or not rating:
        messages.error(request, "Invalid feedback submission: missing item or rating.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError()
    except ValueError:
        messages.error(request, "Invalid rating value.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    
    # Check if feedback already exists for this order item
    if hasattr(order_item, 'feedback'):
        messages.error(request, "You have already submitted feedback for this item.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    # Get buyer name
    buyer_name = "Guest Buyer"
    if order_item.order.user:
        buyer_name = order_item.order.user.get_full_name() or order_item.order.user.username
    elif order_item.order.guest_name:
        buyer_name = order_item.order.guest_name
        
    user = request.user if request.user.is_authenticated else None
    
    # Create feedback
    feedback = Feedback.objects.create(
        product=order_item.product,
        order_item=order_item,
        user=user,
        buyer_name=buyer_name,
        rating=rating,
        comment=comment
    )
    
    # Save uploaded images (pics)
    images = request.FILES.getlist('pics')
    for img in images:
        FeedbackImage.objects.create(feedback=feedback, image=img)
        
    # Recalculate product average rating and review count
    product = order_item.product
    feedbacks = Feedback.objects.filter(product=product)
    count = feedbacks.count()
    if count > 0:
        avg_rating = sum(f.rating for f in feedbacks) / count
        product.rating = round(avg_rating, 1)
        product.review_count = count
        product.save()
        
    messages.success(request, f"Feedback submitted successfully for {product.name}!")
    return redirect(request.META.get('HTTP_REFERER', '/'))


