"""
Checkout views: Start → Address+Map → Payment → Confirm → Track
"""
import json
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
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


def _get_base_url(request=None):
    """Derive base URL for email links."""
    if request:
        return request.build_absolute_uri('/')[:-1]
    return 'http://127.0.0.1:8000'


def _send_admin_order_email(order, request=None):
    """Send full internal order alert to company email."""
    company_email = _get_from_email()
    if not company_email:
        return

    base_url = _get_base_url(request)
    admin_order_url = f"{base_url}/portal/admin/orders/{order.id}/"

    items = order.items.select_related('product').all()
    order_items = []
    items_text_list = []
    for item in items:
        subtotal = item.price_at_purchase * item.quantity
        order_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'price_at_purchase': item.price_at_purchase,
            'subtotal': subtotal
        })
        items_text_list.append(f"  • {item.product.name} (x{item.quantity}) — Rs. {item.price_at_purchase:,.0f} each [Subtotal: Rs. {subtotal:,.0f}]")

    items_text = '\n'.join(items_text_list)
    maps_text = f"\n🗺️  Map Location: {order.maps_link}" if order.maps_link else ""

    payment_labels = dict(Order.PAYMENT_CHOICES)
    payment_display = payment_labels.get(order.payment_method, order.payment_method)

    # Classy Plain Text Version
    plain_message = (
        f"📦 NEW ORDER RECEIVED — #{order.id}\n"
        f"{'='*50}\n\n"
        f"👤 CUSTOMER DETAILS\n"
        f"  • Name   : {order.customer_name}\n"
        f"  • Email  : {order.customer_email}\n"
        f"  • Phone  : {order.customer_phone}\n"
        f"  • Type   : {'Guest Checkout' if order.is_guest else 'Registered Customer'}\n\n"
        f"📍 DELIVERY ADDRESS\n"
        f"  • House/Flat : {order.house_number}\n"
        f"  • Street/Col : {order.street_colony}\n"
        f"  • City       : {order.city}\n"
        f"  • Landmark   : {order.landmark or 'None'}\n"
        f"{maps_text}\n\n"
        f"📱 ORDERED ITEMS\n"
        f"{items_text}\n\n"
        f"💳 Payment Method : {payment_display}\n"
        f"💰 Total Amount    : Rs. {order.total_amount:,.0f}\n"
        f"🕐 Order Time      : {order.created_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"🔐 Open in Admin Portal:\n"
        f"{admin_order_url}\n"
    )

    # Rich HTML Version
    context = {
        'order': order,
        'order_items': order_items,
        'payment_display': payment_display,
        'admin_order_url': admin_order_url,
    }
    html_message = None
    try:
        html_message = render_to_string('emails/order_admin.html', context)
    except Exception as e:
        print("Error rendering admin email template:", e)

    try:
        send_custom_email(
            subject=f"[New Order #{order.id}] {order.customer_name} — Rs. {order.total_amount:,.0f}",
            message=plain_message,
            recipient_list=[company_email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print("Admin email error:", e)


def _send_customer_order_email(order, request=None):
    """Send classy confirmation email to customer (Strictly NO admin URLs or sensitive details)."""
    customer_email = order.customer_email
    if not customer_email:
        return

    base_url = _get_base_url(request)
    company_email = SiteSettings.get_email()
    company_phone = SiteSettings.get_phone()

    items = order.items.select_related('product').all()
    order_items = []
    items_text_list = []
    for item in items:
        subtotal = item.price_at_purchase * item.quantity
        order_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'price_at_purchase': item.price_at_purchase,
            'subtotal': subtotal
        })
        items_text_list.append(f"  • {item.product.name} x{item.quantity} — Rs. {item.price_at_purchase:,.0f} (Rs. {subtotal:,.0f})")

    items_text = '\n'.join(items_text_list)

    payment_labels = dict(Order.PAYMENT_CHOICES)
    payment_display = payment_labels.get(order.payment_method, order.payment_method)

    if order.is_guest:
        tracking_url = f"{base_url}/track/{order.tracking_token}/"
        tracking_line = f"Track your live order status here:\n{tracking_url}"
    else:
        tracking_url = f"{base_url}/account/orders/"
        tracking_line = f"Track all your orders in your dashboard:\n{tracking_url}"

    email_line = f"✉️ Email: {company_email}\n" if company_email else ""

    # Classy Plain Text Version (strictly customer-facing)
    plain_message = (
        f"Dear {order.customer_name},\n\n"
        f"Thank you for choosing Madina Mobile Shop! Your order has been placed successfully.\n\n"
        f"ORDER SUMMARY\n"
        f"{'─'*40}\n"
        f"Order Number   : #{order.id}\n"
        f"Order Date     : {order.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
        f"Payment Method : {payment_display}\n\n"
        f"ORDERED ITEMS\n"
        f"{items_text}\n\n"
        f"Total Amount   : Rs. {order.total_amount:,.0f}\n\n"
        f"DELIVERY ADDRESS\n"
        f"{order.full_address}\n\n"
        f"ORDER TRACKING\n"
        f"{tracking_line}\n\n"
        f"Our team will confirm your order and dispatch your package shortly.\n\n"
        f"If you have any questions, feel free to contact us:\n"
        f"📞 Phone: {company_phone}\n"
        f"{email_line}"
        f"Warm regards,\n"
        f"Madina Mobile Shop — Customer Support\n"
        f"{base_url}/\n"
    )

    # Rich HTML Version
    context = {
        'order': order,
        'order_items': order_items,
        'payment_display': payment_display,
        'tracking_url': tracking_url,
        'company_phone': company_phone,
        'company_email': company_email,
        'current_year': timezone.now().year,
    }
    html_message = None
    try:
        html_message = render_to_string('emails/order_customer.html', context)
    except Exception as e:
        print("Error rendering customer email template:", e)

    try:
        send_custom_email(
            subject=f"Order Confirmed #{order.id} — Madina Mobile Shop",
            message=plain_message,
            recipient_list=[customer_email],
            html_message=html_message,
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
            _send_customer_order_email(order, request=request)
            _send_admin_order_email(order, request=request)

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
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'items__feedback__images'),
        tracking_token=token
    )
    return render(request, 'checkout/track.html', {'order': order})


# ─── Track Order Search (public form) ────────────────────────────────────────

def track_order_search(request):
    """Public page where anyone can enter a tracking token to see their order."""
    error = None
    if request.method == 'POST':
        token_input = request.POST.get('tracking_token', '').strip()
        if not token_input:
            error = 'Please enter your Order Tracking ID.'
        else:
            try:
                # Accept both the full UUID and the short order ID fallback
                import uuid as _uuid
                try:
                    token_uuid = _uuid.UUID(str(token_input))
                    order = Order.objects.filter(tracking_token=token_uuid).first()
                except ValueError:
                    # Maybe user typed numeric order ID
                    order = Order.objects.filter(id=token_input).first()

                if order:
                    return redirect('track_order', token=str(order.tracking_token))
                else:
                    error = 'No order found with that Tracking ID. Please check and try again.'
            except Exception:
                error = 'Invalid Tracking ID format. Please check the ID from your order confirmation email.'

    return render(request, 'checkout/track_search.html', {'error': error})

