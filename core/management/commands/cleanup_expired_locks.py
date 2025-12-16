from django.core.management.base import BaseCommand
from core.models import SeatLock

class Command(BaseCommand):
    help = 'Clean up expired seat locks from the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning up expired seat locks...')
        
        # Release expired locks using the model method
        count = SeatLock.release_expired_locks()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully removed {count} expired seat locks.')
        )