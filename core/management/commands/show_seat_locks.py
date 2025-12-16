from django.core.management.base import BaseCommand
from core.models import SeatLock
from django.utils import timezone
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Display current seat locks in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-expired',
            action='store_true',
            help='Include expired locks in the output',
        )

    def handle(self, *args, **options):
        show_expired = options['show_expired']
        
        self.stdout.write('Current Seat Locks Report')
        self.stdout.write('=' * 50)
        
        # Get all locks
        locks = SeatLock.objects.all().select_related('show__movie', 'user')
        
        # Filter out expired if not requested
        if not show_expired:
            locks = locks.filter(expires_at__gt=timezone.now())
        
        if not locks.exists():
            self.stdout.write('No seat locks found.')
            return
        
        # Group by status
        active_locks = []
        expired_locks = []
        
        now = timezone.now()
        for lock in locks:
            if lock.expires_at > now:
                active_locks.append(lock)
            else:
                expired_locks.append(lock)
        
        # Display active locks
        self.stdout.write(f'\nActive Locks ({len(active_locks)}):')
        self.stdout.write('-' * 30)
        if active_locks:
            for lock in active_locks:
                time_left = lock.expires_at - now
                minutes_left = int(time_left.total_seconds() // 60)
                self.stdout.write(
                    f'  {lock.seat_number} - {lock.show.movie.title} - '
                    f'{lock.user.username} - Expires in {minutes_left} minutes'
                )
        else:
            self.stdout.write('  None')
        
        # Display expired locks if requested
        if show_expired:
            self.stdout.write(f'\nExpired Locks ({len(expired_locks)}):')
            self.stdout.write('-' * 30)
            if expired_locks:
                for lock in expired_locks:
                    time_since_expired = now - lock.expires_at
                    minutes_since = int(time_since_expired.total_seconds() // 60)
                    self.stdout.write(
                        f'  {lock.seat_number} - {lock.show.movie.title} - '
                        f'{lock.user.username} - Expired {minutes_since} minutes ago'
                    )
            else:
                self.stdout.write('  None')
        
        self.stdout.write(f'\nTotal Locks: {locks.count()}')