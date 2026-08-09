"""
Checkout views: Start → Address+Map → Payment → Confirm → Track
"""
import json
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from store.email_utils import send_custom_email
from django.conf import settings as django_settings
from django.views.decorators.http import require_POST
from store.models import Product, SiteSettings
from accounts.models import Order, OrderItem

# ─── Pakistan Cities ──────────────────────────────────────────────────────────
PAKISTAN_CITIES = [
    'Islamabad', 'Rawalpindi', 'Lahore', 'Karachi', 'Faisalabad',
    'Multan', 'Gujranwala', 'Hyderabad', 'Peshawar', 'Quetta',
    'Sialkot', 'Bahawalpur', 'Sargodha', 'Sukkur', 'Larkana',
    'Sheikhupura', 'Jhang', 'Rahim Yar Khan', 'Gujrat', 'Kasur',
    'Mardan', 'Mingora', 'Abbottabad', 'Sahiwal', 'Okara',
    'Mirpur Khas', 'Nawabshah', 'Chiniot', 'Kotri', 'Khanewal',
    'Hafizabad', 'Muzaffargarh', 'Jhelum', 'Sadiqabad', 'Wah Cantonment',
    'Attock', 'Mandi Bahauddin', 'Bahawalnagar', 'Muridke', 'Pakpattan',
    'Other',
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_from_email():
    """Get company email from SiteSettings, fallback to Django default."""
    email = SiteSettings.get_email()
    return email or django_settings.DEFAULT_FROM_EMAIL


def _send_admin_order_email(order):
    """Send full order details to company email."""
    company_email = _get_from_email()
    if not company_email:
        return

    items_text = '\n'.join(
        f"  • {item.product.name} (x{item.quantity}) — Rs. {item.price_at_purchase:,.0f} each"
        for item in order.items.select_related('product').all()
    )

    maps_text = f"\n🗺️  Map Location: {order.maps_link}" if order.maps_link else ""

    payment_labels = dict(Order.PAYMENT_CHOICES)
    payment_display = payment_labels.get(order.payment_method, order.payment_method)

    message = (
        f"📦 NEW ORDER #{order.id} — Madina Mobile Shop\n"
        f"{'='*50}\n\n"
        f"🧑 CUSTOMER INFO\n"
        f"  Name   : {order.customer_name}\n"
        f"  Email  : {order.customer_email}\n"
        f"  Phone  : {order.customer_phone}\n"
        f"  Type   : {'Guest' if order.is_guest else 'Registered Customer'}\n\n"
        f"📍 DELIVERY ADDRESS\n"
        f"  House  : {order.house_number}\n"
        f"  Street : {order.street_colony}\n"
        f"  City   : {order.city}\n"
        f"  Landmark: {order.landmark or '—'}\n"
        f"{maps_text}\n\n"
        f"📱 ORDERED ITEMS\n"
        f"{items_text}\n\n"
        f"  Total  : Rs. {order.total_amount:,.0f}\n\n"
        f"💳 PAYMENT METHOD: {payment_display}\n\n"
        f"🕐 Order Time: {order.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
        f"🔗 Admin Portal: http://127.0.0.1:8000/sv-cd6n-lugl/orders/{order.id}/\n"
    )

    try:
        send_custom_email(
            subject=f"[Madina Mobile] New Order #{order.id} — {order.customer_name}",
            message=message,
            recipient_list=[company_email],
            fail_silently=True,
        )
    except Exception as e:
        print("Admin email error:", e)


def _send_customer_order_email(order):
    """Send confirmation email to customer."""
    customer_email = order.customer_email
    if not customer_email:
        return

    from_email = _get_from_email()
    items_text = '\n'.join(
        f"  • {item.product.name} x{item.quantity} — Rs. {item.price_at_purchase:,.0f}"
        for item in order.items.select_related('product').all()
    )

    payment_labels = dict(Order.PAYMENT_CHOICES)
    payment_display = payment_labels.get(order.payment_method, order.payment_method)

    if order.is_guest:
        tracking_url = f"http://127.0.0.1:8000/track/{order.tracking_token}/"
        tracking_line = f"Track your order here: {tracking_url}"
    else:
        tracking_line = "Track your order at: http://127.0.0.1:8000/account/orders/"

    message = (
        f"Dear {order.customer_name},\n\n"
        f"Thank you for your order! Your Madina Mobile Shop order has been placed successfully.\n\n"
        f"ORDER DETAILS\n"
        f"{'─'*40}\n"
        f"Order Number : #{order.id}\n"
        f"Payment      : {payment_display}\n\n"
        f"ITEMS ORDERED\n"
        f"{items_text}\n\n"
        f"Total Amount : Rs. {order.total_amount:,.0f}\n\n"
        f"DELIVERY ADDRESS\n"
        f"{order.full_address}\n\n"
        f"ORDER TRACKING\n"
        f"{tracking_line}\n\n"
        f"Our team will confirm your order shortly.\n\n"
        f"Warm regards,\n"
        f"Madina Mobile Shop — Customer Support\n"
        f"http://127.0.0.1:8000/"
    )

    try:
        send_custom_email(
            subject=f"Order #{order.id} Confirmed — Madina Mobile Shop",
            message=message,
            recipient_list=[customer_email],
            fail_silently=True,
        )
    except Exception as e:
        print("Customer email error:", e)


# ─── Checkout Start ────────────────────────────────────────────────────────────

@require_POST
def checkout_start(request):
    """Receives cart JSON from frontend, saves to session, redirects to address."""
    cart_json = request.POST.get('cart', '[]')
    try:
        cart = json.loads(cart_json)
    except Exception:
        cart = []

    if not cart:
        return redirect('home')

    request.session['checkout_cart'] = cart
    return redirect('checkout_address')


# ─── Step 1: Address ──────────────────────────────────────────────────────────

def checkout_address(request):
    cart = request.session.get('checkout_cart', [])
    if not cart:
        return redirect('home')

    error = None

    if request.method == 'POST':
        house_number  = request.POST.get('house_number', '').strip()
        street_colony = request.POST.get('street_colony', '').strip()
        city          = request.POST.get('city', '').strip()
        landmark      = request.POST.get('landmark', '').strip()
        map_lat       = request.POST.get('map_lat', '').strip()
        map_lng       = request.POST.get('map_lng', '').strip()

        # Guest-only fields
        guest_name  = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        guest_phone = request.POST.get('guest_phone', '').strip()

        # Validation
        if not house_number or not street_colony or not city:
            error = 'Please fill in your House Number, Street/Colony, and City.'
        elif not request.user.is_authenticated and not all([guest_name, guest_email, guest_phone]):
            error = 'Please enter your Name, Email, and Phone Number.'
        else:
            request.session['checkout_address'] = {
                'house_number': house_number,
                'street_colony': street_colony,
                'city': city,
                'landmark': landmark,
                'map_lat': map_lat,
                'map_lng': map_lng,
                'guest_name': guest_name,
                'guest_email': guest_email,
                'guest_phone': guest_phone,
            }
            return redirect('checkout_payment')

    # Pre-fill from profile for logged-in users
    prefill = {}
    if request.user.is_authenticated:
        try:
            p = request.user.profile
            prefill = {
                'city': p.city,
                'address': p.address,
            }
        except Exception:
            pass

    # Cart total
    total = sum(float(item.get('price', 0)) * int(item.get('qty', 1)) for item in cart)

    return render(request, 'checkout/address.html', {
        'cart': cart,
        'total': total,
        'cities': PAKISTAN_CITIES,
        'prefill': prefill,
        'error': error,
        'is_guest': not request.user.is_authenticated,
    })


# ─── Step 2: Payment ──────────────────────────────────────────────────────────

def checkout_payment(request):
    cart    = request.session.get('checkout_cart', [])
    address = request.session.get('checkout_address', {})

    if not cart or not address:
        return redirect('checkout_address')

    error = None

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', '').strip()
        valid_methods = [c[0] for c in Order.PAYMENT_CHOICES]

        if payment_method not in valid_methods:
            error = 'Please select a payment method.'
        else:
            # ── Create Order ──────────────────────────────────────────────────
            total = sum(
                Decimal(str(item.get('price', 0))) * int(item.get('qty', 1))
                for item in cart
            )

            order = Order(
                total_amount=total,
                payment_method=payment_method,
                house_number=address.get('house_number', ''),
                street_colony=address.get('street_colony', ''),
                city=address.get('city', ''),
                landmark=address.get('landmark', ''),
                guest_name=address.get('guest_name', ''),
                guest_email=address.get('guest_email', ''),
                guest_phone=address.get('guest_phone', ''),
            )

            # Map coordinates
            try:
                order.map_lat = Decimal(address['map_lat']) if address.get('map_lat') else None
                order.map_lng = Decimal(address['map_lng']) if address.get('map_lng') else None
            except Exception:
                pass

            # Assign user if logged in
            if request.user.is_authenticated:
                order.user = request.user

            order.save()

            # Create OrderItems
            for item in cart:
                try:
                    product = Product.objects.filter(name=item['name']).first()
                    if not product:
                        product = Product.objects.first()
                    if product:
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=int(item.get('qty', 1)),
                            price_at_purchase=Decimal(str(item.get('price', product.sale_price))),
                        )
                except Exception as e:
                    print("Order item error:", e)

            # Clear session cart
            for key in ['checkout_cart', 'checkout_address']:
                request.session.pop(key, None)

            # Send emails
            _send_customer_order_email(order)
            _send_admin_order_email(order)

            return redirect('checkout_confirm', token=str(order.tracking_token))

    total = sum(float(item.get('price', 0)) * int(item.get('qty', 1)) for item in cart)

    company_phone = SiteSettings.get_phone()

    return render(request, 'checkout/payment.html', {
        'cart': cart,
        'total': total,
        'address': address,
        'payment_choices': Order.PAYMENT_CHOICES,
        'company_phone': company_phone,
        'error': error,
    })


from urllib.parse import quote


# ─── Confirmation ─────────────────────────────────────────────────────────────

def checkout_confirm(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    
    whatsapp_url = None
    if order.payment_method in ['bank', 'easypaisa', 'jazzcash']:
        phone = SiteSettings.get_whatsapp_phone()
        payment_name = order.get_payment_method_display()
        items_list = ", ".join([f"{item.product.name} (x{item.quantity})" for item in order.items.all()]) or "Mobile Purchase"
        
        msg = (
            f"Hello Madina Mobile Shop! 📱\n\n"
            f"I have placed an order on your website:\n"
            f"• Order ID: #{order.id}\n"
            f"• Customer Name: {order.customer_name}\n"
            f"• Phone Number: {order.customer_phone}\n"
            f"• Payment Method: {payment_name}\n"
            f"• Total Amount: Rs. {int(order.total_amount):,}\n"
            f"• Items: {items_list}\n"
            f"• City: {order.city}\n\n"
            f"Please send me your {payment_name} account details so I can complete payment. Thank you!"
        )
        whatsapp_url = f"https://wa.me/{phone}?text={quote(msg)}"

    return render(request, 'checkout/confirm.html', {
        'order': order,
        'whatsapp_url': whatsapp_url,
        'company_phone': SiteSettings.get_phone(),
    })


# ─── Guest Order Tracking ─────────────────────────────────────────────────────

def track_order(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    return render(request, 'checkout/track.html', {'order': order})
