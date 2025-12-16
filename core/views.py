"""
Views for BookMyShow clone
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db.models import Sum, Count, Q
from datetime import timedelta
from email.mime.image import MIMEImage
import json
import random
import razorpay
import qrcode
from io import BytesIO

from .models import Movie, Show, Cinema, Screen, Seat, Booking, SeatLock, UserProfile, Wallet
from .forms import UserRegistrationForm, MovieForm


# ---- Role helpers ----

def _get_user_role(user):
    if not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return None

def _has_approved_role(user, role):
    if not user.is_authenticated:
        return False
    try:
        return user.profile.has_role(role)
    except UserProfile.DoesNotExist:
        return False


def is_organizer(user):
    return _has_approved_role(user, UserProfile.ROLE_ORGANIZER)


def is_staff_role(user):
    return _has_approved_role(user, UserProfile.ROLE_STAFF)


def home(request):
    """Home page - Movies list with filters"""
    # Order by promoted status first, then by creation date
    movies = Movie.objects.all().order_by('-is_promoted', '-created_at')
    
    # Get filter parameters
    genre = request.GET.get('genre')
    language = request.GET.get('language')
    q = request.GET.get('q')
    
    # Apply filters
    if genre:
        movies = movies.filter(genre=genre)
    if language:
        movies = movies.filter(language=language)
    if q:
        movies = movies.filter(title__icontains=q)
    
    # Get unique genres and languages for filters
    genres = Movie.GENRES
    languages = Movie.LANGUAGES
    
    context = {
        'movies': movies,
        'genres': genres,
        'languages': languages,
        'selected_genre': genre,
        'selected_language': language,
        'search_query': q,
    }
    return render(request, 'core/movies.html', context)


@require_http_methods(["GET"])
def movies_list_api(request):
    """AJAX endpoint to return filtered movies HTML fragment."""
    # Order by promoted status first, then by creation date
    movies = Movie.objects.all().order_by('-is_promoted', '-created_at')

    genre = request.GET.get('genre')
    language = request.GET.get('language')
    q = request.GET.get('q')

    if genre:
        movies = movies.filter(genre=genre)
    if language:
        movies = movies.filter(language=language)
    if q:
        movies = movies.filter(title__icontains=q)

    # Render only the movies grid partial
    from django.template.loader import render_to_string

    html = render_to_string('core/_movies_grid.html', {
        'movies': movies,
    }, request=request)

    response = JsonResponse({'success': True, 'html': html})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response

@require_http_methods(["GET"])
def movies_meta_api(request):
    """Return genres and languages for the frontend filters."""
    data = {
        'genres': list(Movie.GENRES),
        'languages': list(Movie.LANGUAGES),
    }
    response = JsonResponse({'success': True, **data})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response

def welcome_page(request):
    return render(request, 'core/welcome.html')

def movie_detail(request, movie_id):
    """Movie detail page with trailer and shows"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Get upcoming shows for this movie
    today = timezone.now().date()
    shows = Show.objects.filter(
        movie=movie,
        date__gte=today
    ).select_related('screen__cinema').order_by('date', 'start_time')
    
    context = {
        'movie': movie,
        'shows': shows,
    }
    return render(request, 'core/movie_detail.html', context)


@login_required
def show_page(request, show_id):
    """Show page with seat map"""
    show = get_object_or_404(Show, id=show_id)
    
    # Release expired locks
    SeatLock.release_expired_locks()
    
    # Get all seats for this screen
    seats = show.screen.seats.all().order_by('number')
    
    # Get seat states
    booked_seats = show.get_booked_seats()
    locked_seats = show.get_locked_seats()
    available_seats = show.get_available_seats()
    
    # Get user's locked seats for this show
    user_locks = SeatLock.objects.filter(
        show=show,
        user=request.user,
        expires_at__gt=timezone.now()
    )
    user_locked_seats = list(user_locks.values_list('seat_number', flat=True))
    
    # Organize seats in a grid (assuming naming like A1, A2, B1, B2, etc.)
    seat_grid = {}
    for seat in seats:
        row = seat.number[0]  # First character is row
        if row not in seat_grid:
            seat_grid[row] = []
        
        seat_status = 'available'
        if seat.number in booked_seats:
            seat_status = 'booked'
        elif seat.number in locked_seats:
            if seat.number in user_locked_seats:
                seat_status = 'user_locked'
            else:
                seat_status = 'locked'
        
        seat_grid[row].append({
            'number': seat.number,
            'type': seat.seat_type,
            'status': seat_status
        })
    
    context = {
        'show': show,
        'seat_grid': dict(sorted(seat_grid.items())),
        'price': show.price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'core/show.html', context)


@login_required
@require_http_methods(["POST"])
def lock_seats(request):
    """API endpoint to lock seats"""
    try:
        data = json.loads(request.body)
        show_id = data.get('show_id')
        seat_numbers = data.get('seats', [])
        
        if not show_id or not seat_numbers:
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
        
        show = get_object_or_404(Show, id=show_id)
        
        # Release expired locks first
        SeatLock.release_expired_locks()
        
        with transaction.atomic():
            # Check if seats are available
            booked_seats = show.get_booked_seats()
            locked_seats = show.get_locked_seats()
            
            for seat_number in seat_numbers:
                if seat_number in booked_seats:
                    return JsonResponse({
                        'success': False,
                        'error': f'Seat {seat_number} is already booked'
                    }, status=400)
                
                if seat_number in locked_seats:
                    # Check if locked by another user
                    lock = SeatLock.objects.filter(
                        show=show,
                        seat_number=seat_number,
                        expires_at__gt=timezone.now()
                    ).first()
                    
                    if lock and lock.user != request.user:
                        return JsonResponse({
                            'success': False,
                            'error': f'Seat {seat_number} is locked by another user'
                        }, status=400)
            
            # Remove user's previous locks for this show
            SeatLock.objects.filter(show=show, user=request.user).delete()
            
            # Create new locks
            expires_at = timezone.now() + timedelta(minutes=settings.SEAT_LOCK_DURATION)
            for seat_number in seat_numbers:
                SeatLock.objects.create(
                    show=show,
                    seat_number=seat_number,
                    user=request.user,
                    expires_at=expires_at
                )
            
            return JsonResponse({
                'success': True,
                'message': f'{len(seat_numbers)} seats locked successfully',
                'expires_at': expires_at.isoformat()
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_order(request):
    """Create Razorpay order for payment"""
    try:
        data = json.loads(request.body)
        show_id = data.get('show_id')
        seat_numbers = data.get('seats', [])
        
        if not show_id or not seat_numbers:
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
        
        show = get_object_or_404(Show, id=show_id)
        
        # Verify seats are locked by this user
        user_locks = SeatLock.objects.filter(
            show=show,
            user=request.user,
            seat_number__in=seat_numbers,
            expires_at__gt=timezone.now()
        )
        
        if user_locks.count() != len(seat_numbers):
            return JsonResponse({
                'success': False,
                'error': 'Some seats are not locked by you'
            }, status=400)
        
        # Calculate total amount
        total_amount = float(show.price) * len(seat_numbers)
        amount_paise = int(total_amount * 100)  # Razorpay uses paise
        
        # Create Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1
        }
        
        razorpay_order = client.order.create(data=order_data)
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': total_amount,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def confirm_booking(request):
    """Confirm booking after successful payment"""
    try:
        data = json.loads(request.body)
        show_id = data.get('show_id')
        seat_numbers = data.get('seats', [])
        payment_id = data.get('payment_id')
        
        if not show_id or not seat_numbers:
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
        
        show = get_object_or_404(Show, id=show_id)
        
        # Release expired locks
        SeatLock.release_expired_locks()
        
        with transaction.atomic():
            # Verify all seats are locked by this user
            user_locks = SeatLock.objects.filter(
                show=show,
                user=request.user,
                seat_number__in=seat_numbers,
                expires_at__gt=timezone.now()
            )
            
            if user_locks.count() != len(seat_numbers):
                return JsonResponse({
                    'success': False,
                    'error': 'Seats are not properly locked'
                }, status=400)
            
            # Check no seats are already booked
            booked_seats = show.get_booked_seats()
            for seat in seat_numbers:
                if seat in booked_seats:
                    return JsonResponse({
                        'success': False,
                        'error': f'Seat {seat} is already booked'
                    }, status=400)
            
            # Calculate total amount
            total_amount = show.price * len(seat_numbers)
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                show=show,
                seats=json.dumps(seat_numbers),
                total_amount=total_amount,
                status='confirmed'
            )
            
            # Remove seat locks
            user_locks.delete()
            
            # Send confirmation email
            try:
                send_booking_email(request.user, booking)
            except Exception as e:
                # Log the error but don't fail the booking
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send booking email: {e}", exc_info=True)
            
            return JsonResponse({
                'success': True,
                'booking_id': str(booking.booking_id),
                'message': 'Booking confirmed successfully'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def send_booking_email(user, booking):
    """Send booking confirmation email with QR code"""
    import qrcode
    from io import BytesIO
    from django.core.mail import EmailMultiAlternatives
    from email.mime.image import MIMEImage

    subject = f'Booking Confirmation - {booking.show.movie.title}'
    
    seats_list = booking.get_seats_list()
    seats_str = ', '.join(seats_list)
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(str(booking.booking_id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image_data = buffer.getvalue()

    # Plain text message
    text_content = f"""
Dear {user.username},

Thank you for booking with BookMyShow! Your booking has been confirmed.

Booking Details:
================
Booking ID: {booking.booking_id}
Movie: {booking.show.movie.title}
Cinema: {booking.show.screen.cinema.name}
Screen: {booking.show.screen.name}
Date: {booking.show.date}
Time: {booking.show.start_time}
Seats: {seats_str}
Total Amount: ₹{booking.total_amount}

Please present this QR code at the cinema entrance for ticket validation.

Have a great movie experience!

Best regards,
BookMyShow Team
"""

    # HTML message with embedded image
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">Booking Confirmed!</h1>
                </div>
                
                <div style="padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd;">
                    <p>Dear <strong>{user.username}</strong>,</p>
                    
                    <p>Thank you for booking with BookMyShow! Your booking has been confirmed.</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #eee; margin: 20px 0;">
                        <h2 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">Booking Details</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Booking ID:</td>
                                <td style="padding: 8px;">{booking.booking_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Movie:</td>
                                <td style="padding: 8px;">{booking.show.movie.title}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Cinema:</td>
                                <td style="padding: 8px;">{booking.show.screen.cinema.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Screen:</td>
                                <td style="padding: 8px;">{booking.show.screen.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Date:</td>
                                <td style="padding: 8px;">{booking.show.date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Time:</td>
                                <td style="padding: 8px;">{booking.show.start_time}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Seats:</td>
                                <td style="padding: 8px;">{seats_str}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Total Amount:</td>
                                <td style="padding: 8px;">₹{booking.total_amount}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p><strong>Please present this QR code at the cinema entrance:</strong></p>
                        <img src="cid:qrcode_image" alt="Booking QR Code" style="width: 200px; height: 200px; border: 1px solid #ddd; padding: 10px; background: white;">
                    </div>
                    
                    <p style="text-align: center; font-style: italic;">
                        Have a great movie experience!
                    </p>
                </div>
                
                <div style="background-color: #333; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
                    <p>BookMyShow - Your ultimate movie ticket booking platform</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    # Attach QR code
    image = MIMEImage(qr_image_data)
    image.add_header('Content-ID', '<qrcode_image>')
    msg.attach(image)
    
    msg.send(fail_silently=True)


def send_show_reminder_email(user, booking):
    """Send reminder email for upcoming show"""
    from django.core.mail import EmailMultiAlternatives
    from email.mime.image import MIMEImage
    import qrcode
    from io import BytesIO

    subject = f'Reminder: Your show "{booking.show.movie.title}" is tomorrow!'
    
    seats_list = booking.get_seats_list()
    seats_str = ', '.join(seats_list)
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(str(booking.booking_id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image_data = buffer.getvalue()

    # Plain text message
    text_content = f"""
Dear {user.username},

This is a friendly reminder that your movie show is tomorrow!

Booking Details:
================
Booking ID: {booking.booking_id}
Movie: {booking.show.movie.title}
Cinema: {booking.show.screen.cinema.name}
Screen: {booking.show.screen.name}
Date: {booking.show.date}
Time: {booking.show.start_time}
Seats: {seats_str}
Total Amount: ₹{booking.total_amount}

Please arrive at least 15 minutes before the show time.

Have a great movie experience!

Best regards,
BookMyShow Team
"""

    # HTML message
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #3498db; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">Show Reminder</h1>
                </div>
                
                <div style="padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd;">
                    <p>Dear <strong>{user.username}</strong>,</p>
                    
                    <p>This is a friendly reminder that your movie show is <strong>tomorrow</strong>!</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #eee; margin: 20px 0;">
                        <h2 style="color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Booking Details</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Booking ID:</td>
                                <td style="padding: 8px;">{booking.booking_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Movie:</td>
                                <td style="padding: 8px;">{booking.show.movie.title}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Cinema:</td>
                                <td style="padding: 8px;">{booking.show.screen.cinema.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Screen:</td>
                                <td style="padding: 8px;">{booking.show.screen.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Date:</td>
                                <td style="padding: 8px;">{booking.show.date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Time:</td>
                                <td style="padding: 8px;">{booking.show.start_time}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Seats:</td>
                                <td style="padding: 8px;">{seats_str}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Total Amount:</td>
                                <td style="padding: 8px;">₹{booking.total_amount}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; font-weight: bold; color: #856404;">
                            ⏰ Please arrive at least 15 minutes before the show time.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p><strong>Your QR code for entry:</strong></p>
                        <img src="cid:qrcode_image" alt="Booking QR Code" style="width: 200px; height: 200px; border: 1px solid #ddd; padding: 10px; background: white;">
                    </div>
                    
                    <p style="text-align: center; font-style: italic;">
                        Have a great movie experience!
                    </p>
                </div>
                
                <div style="background-color: #333; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
                    <p>BookMyShow - Your ultimate movie ticket booking platform</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    # Attach QR code
    image = MIMEImage(qr_image_data)
    image.add_header('Content-ID', '<qrcode_image>')
    msg.attach(image)
    
    msg.send(fail_silently=False)


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'core/profile.html', context)

@login_required
def user_profile(request):
    profile = getattr(request.user, 'profile', None)
    total_bookings = Booking.objects.filter(user=request.user, status__in=['confirmed', 'used']).count()
    upcoming = Booking.objects.filter(user=request.user, status='confirmed').order_by('show__date', 'show__start_time')[:5]
    wallet_balance = getattr(getattr(request.user, 'wallet', None), 'balance', None)
    context = {
        'profile': profile,
        'total_bookings': total_bookings,
        'upcoming': upcoming,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'core/user_profile.html', context)


def register_view(request):
    """User registration with role selection (organizer/staff require approval)."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until OTP verification
            user.save()
            
            selected_role = form.cleaned_data['role']
            profile = user.profile
            profile.role = selected_role
            requires_approval = selected_role in [
                UserProfile.ROLE_ORGANIZER,
                UserProfile.ROLE_STAFF,
            ]
            profile.is_role_approved = not requires_approval
            profile.save(update_fields=['role', 'is_role_approved'])

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['user_id'] = user.id
            
            # Send OTP email
            send_mail(
                'Verify your account - BookMyShow',
                f'Your OTP is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return redirect('verify_otp')
    else:
        form = UserRegistrationForm()

    return render(request, 'core/register.html', {'form': form})


def verify_otp(request):
    """Verify OTP and activate user account."""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        user_id = request.session.get('user_id')
        
        if not session_otp or not user_id:
            messages.error(request, 'Session expired. Please register again.')
            return redirect('register')
            
        if entered_otp == session_otp:
            from django.contrib.auth.models import User
            user = get_object_or_404(User, id=user_id)
            user.is_active = True
            user.save()
            
            # Clear session data
            del request.session['otp']
            del request.session['user_id']
            
            # Check for role approval
            profile = user.profile
            if not profile.is_role_approved:
                messages.success(
                    request,
                    'Account verified! An admin will review your organizer/staff access shortly.'
                )
                return redirect('login')
                
            login(request, user)
            messages.success(request, 'Account verified successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            
    return render(request, 'core/verify_otp.html')


def _login_portal(request, *, expected_role=None, success_url_name=None,
                  heading='Login', subtitle='Access your account to continue.'):
    """Shared login handler used by customer, organizer, and staff portals."""
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            role = _get_user_role(user)
            profile = getattr(user, 'profile', None)
            is_approved = getattr(profile, 'is_role_approved', True)

            if expected_role and (role != expected_role or not is_approved):
                form.add_error(
                    None,
                    'This portal is restricted. Please sign in with the correct account type.'
                )
                if role == expected_role and not is_approved:
                    form.add_error(None, 'Your access is still pending admin approval.')
            else:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')

                if expected_role and success_url_name:
                    return redirect(success_url_name)
                if role in [UserProfile.ROLE_ORGANIZER, UserProfile.ROLE_STAFF] and not is_approved:
                    messages.info(
                        request,
                        'Your special access is still awaiting admin approval. '
                        'You can continue using the platform as a customer.'
                    )
                    return redirect('home')
                if role == UserProfile.ROLE_ORGANIZER and is_approved:
                    return redirect('organizer_dashboard')
                if role == UserProfile.ROLE_STAFF and is_approved:
                    return redirect('staff_scan_ticket')

                return redirect('home')

    context = {
        'form': form,
        'login_heading': heading,
        'login_subtitle': subtitle,
        'portal_role': expected_role,
    }
    return render(request, 'core/login.html', context)


def login_view(request):
    """General login for customers plus role-aware redirect logic."""
    return _login_portal(
        request,
        heading='Login',
        subtitle='Customers log in here. Organizers and staff can also use their dedicated portals.'
    )


def organizer_login_view(request):
    """Dedicated organizer login entry point."""
    return _login_portal(
        request,
        expected_role=UserProfile.ROLE_ORGANIZER,
        success_url_name='organizer_dashboard',
        heading='Organizer Login',
        subtitle='Sign in to create events, manage shows, and view sales snapshots.'
    )


def staff_login_view(request):
    """Dedicated staff / gate scanner login entry point."""
    return _login_portal(
        request,
        expected_role=UserProfile.ROLE_STAFF,
        success_url_name='staff_scan_ticket',
        heading='Staff Login',
        subtitle='Scan tickets, validate entries, and manage guest queues.'
    )


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')


@login_required
def admin_dashboard(request):
    """Admin dashboard with analytics (platform admin, uses Django is_staff)."""
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Total revenue (include both confirmed and used bookings)
    total_revenue = Booking.objects.filter(status__in=['confirmed', 'used']).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Total bookings (include both confirmed and used bookings)
    total_bookings = Booking.objects.filter(status__in=['confirmed', 'used']).count()
    
    # Active seat locks
    active_seat_locks = SeatLock.get_active_locks().count()
    
    # Total users
    from django.contrib.auth.models import User
    total_users = User.objects.count()
    
    # Most popular movies (by ticket count - include both confirmed and used bookings)
    popular_movies = Movie.objects.annotate(
        ticket_count=Count('shows__bookings', filter=Q(shows__bookings__status__in=['confirmed', 'used']))
    ).order_by('-ticket_count')[:10]
    
    # Busiest cinemas (by show bookings - include both confirmed and used bookings)
    busiest_cinemas = Cinema.objects.annotate(
        booking_count=Count('screens__shows__bookings', filter=Q(screens__shows__bookings__status__in=['confirmed', 'used']))
    ).order_by('-booking_count')[:10]
    
    # Recent bookings (include both confirmed and used bookings)
    recent_bookings = Booking.objects.filter(status__in=['confirmed', 'used']).order_by('-created_at')[:20]
    
    context = {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'active_seat_locks': active_seat_locks,
        'total_users': total_users,
        'popular_movies': popular_movies,
        'busiest_cinemas': busiest_cinemas,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'core/admin_dashboard.html', context)


# ---- Organizer dashboard ----

@login_required
@user_passes_test(is_organizer)
def organizer_dashboard(request):
    """Organizer dashboard with analytics and movie management."""
    # Ensure wallet exists
    Wallet.objects.get_or_create(user=request.user)
    
    # Get organizer's movies (include both confirmed and used bookings)
    movies = Movie.objects.filter(organizer=request.user).annotate(
        total_shows=Count('shows'),
        total_bookings=Count('shows__bookings', filter=Q(shows__bookings__status__in=['confirmed', 'used'])),
        revenue=Sum('shows__bookings__total_amount', filter=Q(shows__bookings__status__in=['confirmed', 'used']))
    ).order_by('-created_at')
    
    # Calculate total stats
    total_revenue = movies.aggregate(total=Sum('revenue'))['total'] or 0
    total_tickets = movies.aggregate(total=Sum('total_bookings'))['total'] or 0
    
    context = {
        'movies': movies,
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'wallet_balance': request.user.wallet.balance,
    }
    return render(request, 'core/organizer_dashboard.html', context)


# ---- Staff / Gate scanner page ----

@login_required
@user_passes_test(is_staff_role)
def staff_scan_ticket(request):
    """Very simple ticket validation page for staff (by booking_id)."""
    from uuid import UUID
    booking = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        code = request.POST.get('booking_code', '').strip()
        
        try:
            # Allow both full UUID and first 8 chars
            if len(code) == 8:
                from django.db.models import Q
                booking = Booking.objects.filter(booking_id__startswith=code).first()
            else:
                _ = UUID(code)  # validate UUID format
                booking = Booking.objects.filter(booking_id=code).first()

            if not booking:
                error = 'No booking found for the given code.'
            else:
                if action == 'mark_used':
                    if booking.status == 'confirmed':
                        booking.status = 'used'
                        booking.save()
                        messages.success(request, 'Ticket marked as USED successfully!')
                    elif booking.status == 'used':
                        messages.warning(request, 'Ticket is ALREADY USED.')
                    else:
                        messages.error(request, f'Cannot mark ticket as used. Current status: {booking.status}')
        except Exception:
            error = 'Invalid booking code format.'

    context = {
        'booking': booking,
        'error': error,
    }
    return render(request, 'core/staff_scan.html', context)


# ---- Organizer Movie CRUD ----

@login_required
@user_passes_test(is_organizer)
def organizer_movie_create(request):
    """Create a new movie."""
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            movie = form.save(commit=False)
            movie.organizer = request.user
            movie.save()
            messages.success(request, 'Movie created successfully!')
            return redirect('organizer_dashboard')
    else:
        form = MovieForm()
    
    return render(request, 'core/organizer/movie_form.html', {'form': form, 'title': 'Add New Movie'})


@login_required
@user_passes_test(is_organizer)
def organizer_movie_edit(request, movie_id):
    """Edit an existing movie."""
    movie = get_object_or_404(Movie, id=movie_id, organizer=request.user)
    
    if request.method == 'POST':
        form = MovieForm(request.POST, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, 'Movie updated successfully!')
            return redirect('organizer_dashboard')
    else:
        form = MovieForm(instance=movie)
    
    return render(request, 'core/organizer/movie_form.html', {'form': form, 'title': 'Edit Movie'})


@login_required
@user_passes_test(is_organizer)
def organizer_movie_delete(request, movie_id):
    """Delete a movie."""
    movie = get_object_or_404(Movie, id=movie_id, organizer=request.user)
    
    if request.method == 'POST':
        movie.delete()
        messages.success(request, 'Movie deleted successfully!')
        return redirect('organizer_dashboard')
        
    return render(request, 'core/organizer/movie_confirm_delete.html', {'movie': movie})


# ---- Wallet & Ads ----

@login_required
@user_passes_test(is_organizer)
def wallet_view(request):
    """Manage organizer wallet."""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount', 0)
        try:
            amount = float(amount)
            if amount > 0:
                wallet.add_funds(amount)
                messages.success(request, f'₹{amount} added to wallet successfully!')
                return redirect('wallet_view')
        except ValueError:
            messages.error(request, 'Invalid amount entered.')
            
    return render(request, 'core/organizer/wallet.html', {'wallet': wallet})


@login_required
@user_passes_test(is_organizer)
def promote_movie(request, movie_id):
    """Promote a movie using wallet funds."""
    movie = get_object_or_404(Movie, id=movie_id, organizer=request.user)
    wallet = request.user.wallet
    PROMOTION_COST = 500.00
    
    if request.method == 'POST':
        if movie.is_promoted:
            messages.warning(request, 'This movie is already promoted!')
        elif wallet.deduct_funds(PROMOTION_COST):
            movie.is_promoted = True
            movie.save()
            messages.success(request, 'Movie promoted successfully! It will now appear at the top.')
        else:
            messages.error(request, f'Insufficient funds. Promotion costs ₹{PROMOTION_COST}.')
            
    return redirect('organizer_dashboard')


@login_required
def admin_gift_funds(request):
    """Admin view to gift funds to an organizer."""
    if not request.user.is_staff:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        amount = request.POST.get('amount', 0)
        
        from django.contrib.auth.models import User
        try:
            amount = float(amount)
            user = User.objects.get(username=username)
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet.add_funds(amount)
            messages.success(request, f'Gifted ₹{amount} to {username}!')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except ValueError:
            messages.error(request, 'Invalid amount entered.')
            
    return redirect('admin_dashboard')
