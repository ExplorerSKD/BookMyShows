from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email functionality'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Sending test email to {email}...')
        
        try:
            send_mail(
                'Test Email from BookMyShow',
                'This is a test email to confirm that email functionality is working properly.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent test email to {email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {e}')
            )