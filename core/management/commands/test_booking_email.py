from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Movie, Show, Cinema, Screen, Booking
from core.views import send_booking_email
import json
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test booking confirmation email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test booking email to')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Creating test booking and sending email to {email}...')
        
        try:
            # Get or create a test user
            user, created = User.objects.get_or_create(
                username='email_test_user',
                defaults={
                    'email': email,
                    'first_name': 'Email',
                    'last_name': 'Tester'
                }
            )
            if not created:
                user.email = email
                user.save()
            
            # Get the first movie and show (assuming sample data exists)
            movie = Movie.objects.first()
            show = Show.objects.first()
            
            if not movie or not show:
                self.stdout.write(
                    self.style.ERROR('No movies or shows found. Please populate data first.')
                )
                return
            
            # Create a test booking
            booking = Booking.objects.create(
                user=user,
                show=show,
                seats=json.dumps(['A1', 'A2']),
                total_amount=Decimal('500.00'),
                status='confirmed'
            )
            
            # Send the email
            send_booking_email(user, booking)
            
            # Clean up test booking
            booking.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent test booking email to {email}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send booking email: {e}')
            )
            import traceback
            traceback.print_exc()