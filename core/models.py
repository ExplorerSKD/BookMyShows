"""
Database models for BookMyShow clone
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import json


class UserProfile(models.Model):
    """Profile to extend Django User with a simple role system."""

    ROLE_CUSTOMER = 'CUSTOMER'
    ROLE_ORGANIZER = 'ORGANIZER'
    ROLE_STAFF = 'STAFF'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ORGANIZER, 'Organizer / Venue'),
        (ROLE_STAFF, 'Staff / Gate Scanner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    is_role_approved = models.BooleanField(
        default=True,
        help_text="Only approved roles unlock their special dashboards."
    )

    def __str__(self):
        status = 'approved' if self.is_role_approved else 'pending'
        return f"Profile({self.user.username}, {self.role}, {status})"

    def has_role(self, role):
        return self.role == role and self.is_role_approved


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure every User has an associated UserProfile."""
    try:
        # Safe even if profile already exists; get_or_create won't overwrite role
        UserProfile.objects.get_or_create(user=instance)
    except Exception:
        pass


class Cinema(models.Model):
    """Cinema/Theatre model"""
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city}"


class Screen(models.Model):
    """Screen within a cinema"""
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=100)
    total_seats = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['cinema', 'name']

    def __str__(self):
        return f"{self.cinema.name} - {self.name}"


class Seat(models.Model):
    """Individual seat in a screen"""
    SEAT_TYPES = [
        ('Normal', 'Normal'),
        ('Premium', 'Premium'),
    ]

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats')
    number = models.CharField(max_length=10)  # e.g., A1, A2, B1
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES, default='Normal')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['screen', 'number']
        unique_together = ['screen', 'number']

    def __str__(self):
        return f"{self.screen.name} - Seat {self.number} ({self.seat_type})"


class Movie(models.Model):
    """Movie model"""
    GENRES = [
        ('Action', 'Action'),
        ('Comedy', 'Comedy'),
        ('Romance', 'Romance'),
        ('Drama', 'Drama'),
        ('Thriller', 'Thriller'),
        ('Horror', 'Horror'),
        ('Sci-Fi', 'Sci-Fi'),
        ('Adventure', 'Adventure'),
    ]

    LANGUAGES = [
        ('Hindi', 'Hindi'),
        ('English', 'English'),
        ('Bengali', 'Bengali'),
        ('Tamil', 'Tamil'),
        ('Telugu', 'Telugu'),
        ('Malayalam', 'Malayalam'),
        ('Kannada', 'Kannada'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_mins = models.IntegerField()
    language = models.CharField(max_length=50, choices=LANGUAGES)
    genre = models.CharField(max_length=50, choices=GENRES)
    poster_url = models.URLField(max_length=500, blank=True)
    trailer_url = models.URLField(max_length=500, blank=True)  # YouTube link or embed URL
    
    # New fields for Organizer Panel
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='movies')
    is_promoted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.language})"

    def get_trailer_thumbnail_url(self):
        """Return a YouTube thumbnail URL derived from trailer_url, if possible."""
        if not self.trailer_url:
            return ''

        url = self.trailer_url
        video_id = ''

        # Handle common YouTube URL formats
        # 1) https://www.youtube.com/embed/<id>
        # 2) https://www.youtube.com/watch?v=<id>
        # 3) https://youtu.be/<id>
        try:
            if 'youtube.com/embed/' in url:
                video_id = url.split('youtube.com/embed/')[-1].split('?')[0]
            elif 'youtube.com/watch' in url and 'v=' in url:
                video_id = url.split('v=')[-1].split('&')[0]
            elif 'youtu.be/' in url:
                video_id = url.split('youtu.be/')[-1].split('?')[0]
        except Exception:
            video_id = ''

        if not video_id:
            return ''

        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


class Show(models.Model):
    """Movie show/screening"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='shows')
    date = models.DateField()
    start_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['screen', 'date', 'start_time']

    def __str__(self):
        return f"{self.movie.title} - {self.screen.cinema.name} - {self.date} {self.start_time}"

    def get_available_seats(self):
        """Get list of available seat numbers"""
        all_seats = list(self.screen.seats.values_list('number', flat=True))
        booked_seats = []
        locked_seats = []

        # Get booked seats
        bookings = self.bookings.filter(status='confirmed')
        for booking in bookings:
            try:
                seats = json.loads(booking.seats) if isinstance(booking.seats, str) else booking.seats
                booked_seats.extend(seats)
            except:
                pass

        # Get locked seats (not expired)
        now = timezone.now()
        locks = self.seat_locks.filter(expires_at__gt=now)
        locked_seats = list(locks.values_list('seat_number', flat=True))

        available = [seat for seat in all_seats if seat not in booked_seats and seat not in locked_seats]
        return available

    def get_booked_seats(self):
        """Get list of booked seat numbers"""
        booked_seats = []
        bookings = self.bookings.filter(status='confirmed')
        for booking in bookings:
            try:
                seats = json.loads(booking.seats) if isinstance(booking.seats, str) else booking.seats
                booked_seats.extend(seats)
            except:
                pass
        return booked_seats

    def get_locked_seats(self):
        """Get list of locked seat numbers (not expired)"""
        now = timezone.now()
        locks = self.seat_locks.filter(expires_at__gt=now)
        return list(locks.values_list('seat_number', flat=True))


class Booking(models.Model):
    """Ticket booking"""
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('used', 'Used'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='bookings')
    seats = models.TextField()  # JSON list of seat numbers
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username}"

    def get_seats_list(self):
        """Return seats as a list"""
        try:
            return json.loads(self.seats) if isinstance(self.seats, str) else self.seats
        except:
            return []


class SeatLock(models.Model):
    """Temporary seat lock during booking process"""
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='seat_locks')
    seat_number = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seat_locks')
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ['show', 'seat_number']

    def __str__(self):
        return f"Lock: {self.seat_number} - Show {self.show.id} - User {self.user.username}"

    def is_expired(self):
        """Check if lock has expired"""
        return timezone.now() > self.expires_at

    @classmethod
    def release_expired_locks(cls):
        """Release all expired locks"""
        now = timezone.now()
        expired = cls.objects.filter(expires_at__lte=now)
        count = expired.count()
        expired.delete()
        return count
        
    @classmethod
    def get_active_locks(cls):
        """Get all active (non-expired) locks"""
        now = timezone.now()
        return cls.objects.filter(expires_at__gt=now)


class Wallet(models.Model):
    """Organizer wallet for running ads"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet (₹{self.balance})"

    def add_funds(self, amount):
        from decimal import Decimal
        self.balance += Decimal(str(amount))
        self.save()

    def deduct_funds(self, amount):
        from decimal import Decimal
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False
