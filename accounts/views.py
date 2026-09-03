from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
import random
from django.template.loader import render_to_string
from store.email_utils import send_custom_email
from django.conf import settings
from django.db.models import Q
from .models import CustomerProfile, Cart, Order, OrderItem, EmailVerification


def customer_register(request):
    if request.user.is_authenticated:
        return redirect('customer_profile')

    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([name, email, phone, password]):
            error = 'All fields are required.'
        elif User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            error = 'An account with this email already exists.'
        else:
            # Generate 6-digit Verification OTP Code
            otp_code = str(random.randint(100000, 999999))

            # Store temp registration data with OTP
            EmailVerification.objects.update_or_create(
                email=email,
                defaults={
                    'code': otp_code,
                    'name': name,
                    'phone': phone,
                    'password': password
                }
            )

            # Send Email Verification Code
            subject = "Verify Your Email — Madina Mobile Shop"
            base_url = request.build_absolute_uri('/')[:-1]
            message = (
                f"Hello {name},\n\n"
                f"Thank you for starting your registration with Madina Mobile Shop.\n\n"
                f"Your 6-Digit Email Verification Code is: {otp_code}\n\n"
                f"Please enter this code on the verification page to complete your registration.\n\n"
                f"This code will expire in 10 minutes.\n\n"
                f"Best regards,\n"
                f"Madina Mobile Shop Team\n"
                f"{base_url}/"
            )
            html_message = None
            try:
                html_message = render_to_string('emails/verify_otp.html', {
                    'name': name,
                    'otp_code': otp_code,
                })
            except Exception as e:
                print("OTP email render error:", e)

            try:
                send_custom_email(
                    subject=subject,
                    message=message,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print("Email dispatch error:", e)

            # Redirect to OTP verification page with email in session
            request.session['verify_email'] = email
            return redirect('verify_otp')

    return render(request, 'accounts/register.html', {'error': error})


def verify_otp(request):
    email = request.session.get('verify_email')
    if not email:
        return redirect('customer_register')

    error = None
    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        verification = EmailVerification.objects.filter(email=email).first()

        if not verification or verification.code != entered_code:
            error = 'Invalid verification code. Please check your email and try again.'
        else:
            # Code verified! Create user account & profile now
            name_parts = verification.name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=verification.email,
                email=verification.email,
                password=verification.password,
                first_name=first_name,
                last_name=last_name
            )
            CustomerProfile.objects.create(user=user, phone=verification.phone)

            # Send Organization Confirmation Email
            welcome_subject = "Welcome to Madina Mobile Shop — Account Successfully Created!"
            base_url = request.build_absolute_uri('/')[:-1]
            welcome_message = (
                f"Dear {verification.name},\n\n"
                f"Congratulations! Your customer account with Madina Mobile Shop has been successfully verified and created.\n\n"
                f"Account Details:\n"
                f"• Email: {verification.email}\n"
                f"• Phone: {verification.phone}\n\n"
                f"You can now log in, save items to your cart, track your orders, and enjoy exclusive member offers.\n\n"
                f"Shop Now: {base_url}/\n\n"
                f"Warm regards,\n"
                f"Madina Mobile Shop — Customer Support Team"
            )
            welcome_html = None
            try:
                welcome_html = render_to_string('emails/welcome.html', {
                    'name': verification.name,
                    'email': verification.email,
                    'phone': verification.phone,
                    'store_url': f"{base_url}/",
                })
            except Exception as e:
                print("Welcome email render error:", e)

            try:
                send_custom_email(
                    subject=welcome_subject,
                    message=welcome_message,
                    recipient_list=[verification.email],
                    html_message=welcome_html,
                    fail_silently=True,
                )
            except Exception:
                pass

            # Clean up verification entry and session
            verification.delete()
            del request.session['verify_email']

            # Auto-login after verification
            login(request, user)
            messages.success(request, 'Account successfully created and verified!')
            return redirect('customer_profile')

    return render(request, 'accounts/verify_otp.html', {'email': email, 'error': error})


def customer_login(request):
    if request.user.is_authenticated:
        return redirect('customer_profile')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            error = 'Please enter both email and password.'
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if not user.is_active:
                    error = 'Account is disabled.'
                else:
                    login(request, user)
                    
                    # Merge localStorage cart if sent
                    local_cart = request.POST.get('local_cart')
                    if local_cart:
                        try:
                            items = json.loads(local_cart)
                            for item in items:
                                prod = Product.objects.filter(name=item.get('name')).first()
                                if prod:
                                    cart_item, created = Cart.objects.get_or_create(user=user, product=prod)
                                    if not created:
                                        cart_item.quantity += item.get('qty', 1)
                                    else:
                                        cart_item.quantity = item.get('qty', 1)
                                    cart_item.save()
                        except Exception as e:
                            pass

                    next_url = request.GET.get('next', '')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('customer_profile')
            else:
                error = 'Invalid email or password.'

    return render(request, 'accounts/login.html', {'error': error})


def customer_logout(request):
    logout(request)
    return redirect('home')


@login_required
def customer_profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        profile.phone = phone
        profile.address = address
        profile.city = city
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('customer_profile')

    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'orders': orders
    })


@login_required
def sync_cart(request):
    """API endpoint to get and sync cart items for logged-in customer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('cart', [])
            
            # Sync local items into DB
            for item in items:
                prod = Product.objects.filter(name=item.get('name')).first()
                if prod:
                    cart_item, created = Cart.objects.get_or_create(user=request.user, product=prod)
                    cart_item.quantity = item.get('qty', 1)
                    cart_item.save()
        except Exception:
            pass

    # Return current DB cart
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    cart_data = []
    for item in cart_items:
        cart_data.append({
            'name': item.product.name,
            'img': item.product.image_url,
            'price': float(item.product.sale_price),
            'qty': item.quantity
        })
    return JsonResponse({'cart': cart_data})


def my_orders(request):
    """
    Shows current placed orders and history of orders for the user.
    Supports guest order lookup by Order ID, Phone, Email, or Tracking Token.
    """
    if not request.user.is_authenticated:
        q = request.GET.get('q', '').strip()
        found_orders = []
        if q:
            found_orders = Order.objects.filter(
                Q(id__icontains=q) | Q(guest_email__iexact=q) | Q(guest_phone__icontains=q) | Q(tracking_token__icontains=q)
            ).prefetch_related('items__product', 'items__feedback__images').order_by('-created_at')[:5]
        return render(request, 'accounts/my_orders.html', {
            'is_guest': True,
            'q': q,
            'orders': found_orders,
        })

    user_orders = Order.objects.filter(user=request.user).prefetch_related('items__product', 'items__feedback__images').order_by('-created_at')
    
    active_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery']
    active_orders = [o for o in user_orders if o.status in active_statuses]
    history_orders = [o for o in user_orders if o.status not in active_statuses]

    return render(request, 'accounts/my_orders.html', {
        'is_guest': False,
        'active_orders': active_orders,
        'history_orders': history_orders,
        'all_orders': user_orders,
    })

