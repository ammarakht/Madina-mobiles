from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Banner, Category, SearchLog, ProductView
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


def seed_database():
    """Seed the database with initial categories, products, and banners if empty"""
    # 1. Banners
    if Banner.objects.count() == 0:
        Banner.objects.create(
            title='Introducing',
            subtitle='iPhone 15 Pro Max — Titanium Design — The Ultimate iPhone',
            cta_text='Shop Now',
            cta_link='#best-sellers',
            image_url='https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=1400&h=700&fit=crop&q=80',
            order=0,
            is_active=True
        )
        Banner.objects.create(
            title='Special Offer',
            subtitle='Premium Accessories — Protect & Power Your Devices',
            cta_text='Explore Now',
            cta_link='#flash-sale',
            image_url='https://images.unsplash.com/photo-1608156639585-b3a032ef9689?w=1400&h=700&fit=crop&q=80',
            order=1,
            is_active=True
        )
        Banner.objects.create(
            title='Latest Smart Watches',
            subtitle='Stay Connected On The Go',
            cta_text='View Collection',
            cta_link='#smart-watches',
            image_url='https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=1400&h=700&fit=crop&q=80',
            order=2,
            is_active=True
        )

    # 2. Categories
    if Category.objects.count() == 0:
        categories_data = [
            {'name': 'Smartphones', 'slug': 'smartphones', 'icon': '📱', 'image': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=200&h=200&fit=crop'},
            {'name': 'Accessories', 'slug': 'accessories', 'icon': '🔌', 'image': 'https://images.unsplash.com/photo-1608156639585-b3a032ef9689?w=200&h=200&fit=crop'},
            {'name': 'Smart Watches', 'slug': 'smart-watches', 'icon': '⌚', 'image': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=200&h=200&fit=crop'},
            {'name': 'Audio & Gadgets', 'slug': 'audio-gadgets', 'icon': '🎧', 'image': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200&h=200&fit=crop'},
        ]
        for i, cat in enumerate(categories_data):
            Category.objects.create(
                name=cat['name'],
                slug=cat['slug'],
                icon=cat['icon'],
                order=i
            )

    # 3. Products
    if Product.objects.count() == 0:
        product_images = {
            'men': [
                'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1580910051074-3eb694886505?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1565849906660-4469a5815570?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1573148195900-7845dcb9b127?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=400&h=400&fit=crop',
            ],
            'women': [
                'https://images.unsplash.com/photo-1608156639585-b3a032ef9689?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1622445262465-2481c8573126?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1609592424085-f50a80757a3e?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1628157582853-a796fa650a6a?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1618220179428-22790b461013?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=400&h=400&fit=crop',
            ],
            'couples': [
                'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400&h=400&fit=crop',
            ],
            'smart': [
                'https://images.unsplash.com/photo-1434056886845-dac89ffe9b56?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1517502884422-41eaaced0168?w=400&h=400&fit=crop',
            ],
        }

        # Smartphones (category: 'men')
        for i in range(8):
            names = [
                'iPhone 15 Pro Max', 'Samsung Galaxy S24 Ultra', 'Xiaomi 14 Ultra', 'OnePlus 12',
                'Google Pixel 8 Pro', 'Infinix GT 20 Pro', 'Tecno Camon 30 Premier', 'Realme GT 6'
            ]
            original_prices = [450000, 390000, 310000, 270000, 290000, 95000, 85000, 160000]
            sale_prices = [419999, 364999, 289999, 249999, 269999, 89999, 79999, 149999]
            Product.objects.create(
                name=names[i],
                sku=f"MP-SP-{1000+i}",
                category='smartphones',
                original_price=original_prices[i],
                sale_price=sale_prices[i],
                rating=4.5 + (i % 6) * 0.1,
                review_count=30 + i * 25,
                in_stock=True,
                is_flash_sale=(i == 0 or i == 1),
                is_featured=(i == 2),
                image_url=product_images['men'][i],
                image2_url=product_images['men'][(i+1)%8]
            )

        # Accessories (category: 'women')
        for i in range(8):
            names = [
                'MagSafe Silicone Case', '25W USB-C Fast Charger', '9H Tempered Glass', '20,000mAh Power Bank',
                'Magnetic Ring Stand', '15W Fast Wireless Pad', 'OTG USB-C Adapter', 'Heavy Duty Armor Case'
            ]
            original_prices = [4500, 5500, 1500, 8500, 2500, 6500, 2000, 3500]
            sale_prices = [2999, 3999, 899, 5999, 1499, 4499, 999, 1999]
            Product.objects.create(
                name=names[i],
                sku=f"MP-AC-{2000+i}",
                category='accessories',
                original_price=original_prices[i],
                sale_price=sale_prices[i],
                rating=4.5 + (i % 6) * 0.1,
                review_count=40 + i * 30,
                in_stock=True,
                is_flash_sale=(i == 2),
                is_featured=(i == 0),
                image_url=product_images['women'][i],
                image2_url=product_images['women'][(i+1)%8]
            )

        # Audio & Gadgets (category: 'couples')
        for i in range(4):
            names = [
                'AirPods Pro Gen 2 Clone', 'Galaxy Buds 2 Pro',
                'Anker Soundcore Motion', 'Mi Smart Bluetooth Hub'
            ]
            original_prices = [18000, 24000, 15000, 6000]
            sale_prices = [11999, 17999, 10999, 3999]
            Product.objects.create(
                name=names[i],
                sku=f"MP-GD-{3000+i}",
                category='audio-gadgets',
                original_price=original_prices[i],
                sale_price=sale_prices[i],
                rating=4.7 + (i % 3) * 0.1,
                review_count=20 + i * 15,
                in_stock=True,
                is_flash_sale=(i == 3),
                is_featured=(i == 1),
                image_url=product_images['couples'][i],
                image2_url=product_images['couples'][(i+1)%4]
            )

        # Smart Watches (category: 'smart')
        for i in range(4):
            names = [
                'Apple Watch Series 9 GPS', 'Galaxy Watch 6 Classic LTE',
                'Xiaomi Watch S3', 'Haylou Solar Lite'
            ]
            original_prices = [220000, 95000, 45000, 12000]
            sale_prices = [189999, 79999, 34999, 7999]
            Product.objects.create(
                name=names[i],
                sku=f"MP-SW-{4000+i}",
                category='smart-watches',
                original_price=original_prices[i],
                sale_price=sale_prices[i],
                rating=4.6 + (i % 3) * 0.1,
                review_count=15 + i * 20,
                in_stock=True,
                is_flash_sale=(i == 1),
                is_featured=(i == 0),
                image_url=product_images['smart'][i],
                image2_url=product_images['smart'][(i+1)%4]
            )


def home(request):
    # Ensure database is seeded with beautiful initial records
    seed_database()

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

