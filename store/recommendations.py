from .models import Product, SearchLog
from accounts.models import OrderItem
from django.db.models import Q, Count


def get_customer_recommendations(user, limit=4):
    """
    Generate personalized watch recommendations for a logged-in user
    based on:
    1. Categories of previously purchased watches
    2. Categories related to past search queries
    3. Excludes items already bought
    """
    if not user or not user.is_authenticated:
        return []

    # 1. Get categories from user's order history
    bought_categories = OrderItem.objects.filter(
        order__user=user
    ).values_list('product__category', flat=True).distinct()

    bought_product_ids = OrderItem.objects.filter(
        order__user=user
    ).values_list('product_id', flat=True).distinct()

    # 2. Get search query terms for this user
    searches = SearchLog.objects.filter(user=user).values_list('query', flat=True)[:15]

    search_category_matches = set()
    for query in searches:
        q_lower = query.lower()
        if 'men' in q_lower or 'male' in q_lower:
            search_category_matches.add('men')
        if 'women' in q_lower or 'female' in q_lower or 'lady' in q_lower or 'ladies' in q_lower:
            search_category_matches.add('women')
        if 'couple' in q_lower or 'pair' in q_lower:
            search_category_matches.add('couples')
        if 'smart' in q_lower or 'fit' in q_lower:
            search_category_matches.add('smart')

    target_categories = list(set(list(bought_categories) + list(search_category_matches)))

    # If user has no history yet, fallback to featured/top rated items
    if not target_categories:
        return Product.objects.filter(in_stock=True).order_by('-rating', '-review_count')[:limit]

    # Fetch products in target categories, excluding already bought items
    recommendations = Product.objects.filter(
        category__in=target_categories,
        in_stock=True
    ).exclude(id__in=bought_product_ids).order_by('-rating', '-review_count')[:limit]

    # Fill up to `limit` if needed
    rec_list = list(recommendations)
    if len(rec_list) < limit:
        existing_ids = [p.id for p in rec_list] + list(bought_product_ids)
        fillers = Product.objects.filter(
            in_stock=True
        ).exclude(id__in=existing_ids).order_by('-rating')[:limit - len(rec_list)]
        rec_list.extend(fillers)

    return rec_list
