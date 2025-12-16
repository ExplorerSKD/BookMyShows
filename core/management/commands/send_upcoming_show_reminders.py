from django.core.management.base import BaseCommand
from core.models import Booking
from core.views import send_show_reminder_email
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send reminder emails for shows happening tomorrow'

    def handle(self, *args, **options):
        self.stdout.write('Sending upcoming show reminders...')
        
        # Find bookings for shows happening tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        upcoming_bookings = Booking.objects.filter(
            show__date=tomorrow,
            status='confirmed'
        ).select_related('user', 'show__movie', 'show__screen__cinema')
        
        sent_count = 0
        failed_count = 0
        
        for booking in upcoming_bookings:
            try:
                send_show_reminder_email(booking.user, booking)
                sent_count += 1
                self.stdout.write(
                    f'Sent reminder to {booking.user.email} for {booking.show.movie.title}'
                )
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder to {booking.user.email}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {sent_count} reminders, {failed_count} failed.'
            )
        )