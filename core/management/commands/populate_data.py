from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Cinema, Screen, Seat, Movie, Show
from datetime import date, time, timedelta


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database with sample data...')

        # Create cinemas (idempotent)
        cinema1, _ = Cinema.objects.get_or_create(
            name='PVR Cinemas',
            city='Mumbai',
            defaults={'address': 'Phoenix Marketcity, Kurla, Mumbai'},
        )

        cinema2, _ = Cinema.objects.get_or_create(
            name='INOX',
            city='Delhi',
            defaults={'address': 'Nehru Place, New Delhi'},
        )

        # Create screens (idempotent)
        screen1, _ = Screen.objects.get_or_create(
            cinema=cinema1,
            name='Screen 1',
            defaults={'total_seats': 50},
        )

        screen2, _ = Screen.objects.get_or_create(
            cinema=cinema1,
            name='Screen 2',
            defaults={'total_seats': 40},
        )

        screen3, _ = Screen.objects.get_or_create(
            cinema=cinema2,
            name='Audi 1',
            defaults={'total_seats': 60},
        )

        # Create seats for each screen (idempotent)
        rows = ['A', 'B', 'C', 'D', 'E']

        for screen in [screen1, screen2, screen3]:
            seats_per_row = screen.total_seats // len(rows)
            for row in rows:
                for num in range(1, seats_per_row + 1):
                    seat_type = 'Premium' if row in ['D', 'E'] else 'Normal'
                    Seat.objects.get_or_create(
                        screen=screen,
                        number=f'{row}{num}',
                        defaults={'seat_type': seat_type},
                    )

        # Create movies
        movies_data = [
            {
                'title': 'Jawan',
                'description': 'A high-octane action thriller which outlines the emotional journey of a man who is set to rectify the wrongs in the society.',
                'duration_mins': 169,
                'language': 'Hindi',
                'genre': 'Action',
                'poster_url': 'https://via.placeholder.com/300x450?text=Jawan',
                'trailer_url': 'https://www.youtube.com/embed/CEQ1oKh4d5k'
            },
            {
                'title': 'Oppenheimer',
                'description': 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.',
                'duration_mins': 180,
                'language': 'English',
                'genre': 'Drama',
                'poster_url': 'https://via.placeholder.com/300x450?text=Oppenheimer',
                'trailer_url': 'https://www.youtube.com/embed/uYPbbksJxIg'
            },
            {
                'title': 'Dunki',
                'description': 'Four friends from a village in Punjab share a common dream: to go to England. Their problem is that they have neither the visa nor the ticket.',
                'duration_mins': 161,
                'language': 'Hindi',
                'genre': 'Comedy',
                'poster_url': 'https://via.placeholder.com/300x450?text=Dunki',
                'trailer_url': 'https://www.youtube.com/embed/VZvzvLiGUtw'
            },
            {
                'title': 'Jailer',
                'description': 'A retired jailer goes on a manhunt to find his sons killers. But the road leads him to a familiar, albeit a bit darker place.',
                'duration_mins': 168,
                'language': 'Tamil',
                'genre': 'Thriller',
                'poster_url': 'https://via.placeholder.com/300x450?text=Jailer',
                'trailer_url': 'https://www.youtube.com/embed/C6q1C3ZXWTU'
            },
            {
                'title': 'Animal',
                'description': 'A son seeks retribution for his fathers enemies after they try to murder him.',
                'duration_mins': 201,
                'language': 'Hindi',
                'genre': 'Action',
                'poster_url': 'https://via.placeholder.com/300x450?text=Animal',
                'trailer_url': 'https://www.youtube.com/embed/WrkIR70soxM'
            }
        ]

        movies = []
        for movie_data in movies_data:
            # Use title + language as a natural key to avoid duplicates
            movie, _ = Movie.objects.get_or_create(
                title=movie_data['title'],
                language=movie_data['language'],
                defaults=movie_data,
            )
            movies.append(movie)

        # Create shows for the next 7 days
        today = date.today()
        show_times = [time(10, 0), time(13, 30), time(17, 0), time(20, 30)]
        
        screens = [screen1, screen2, screen3]
        
        # For each screen, date and show_time, assign exactly one movie
        # so that (screen, date, start_time) remains unique.
        for day in range(7):
            show_date = today + timedelta(days=day)
            for s_index, screen in enumerate(screens):
                for t_index, show_time in enumerate(show_times):
                    # Choose a movie in a round-robin fashion
                    movie = movies[(day + s_index + t_index) % len(movies)]
                    price = 250.00 if show_time.hour >= 17 else 200.00
                    Show.objects.get_or_create(
                        movie=movie,
                        screen=screen,
                        date=show_date,
                        start_time=show_time,
                        defaults={'price': price},
                    )

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@bookmyshow.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created (username: admin, password: admin123)'))

        # Create organizer user (application role)
        if not User.objects.filter(username='organizer').exists():
            organizer = User.objects.create_user(
                username='organizer',
                email='organizer@example.com',
                password='organizer123'
            )
            organizer.profile.role = 'ORGANIZER'
            organizer.profile.is_role_approved = True
            organizer.profile.save(update_fields=['role', 'is_role_approved'])
            self.stdout.write(self.style.SUCCESS('Organizer user created (username: organizer, password: organizer123)'))

        # Create staff / gate-scanner user (application role)
        if not User.objects.filter(username='staff').exists():
            staff = User.objects.create_user(
                username='staff',
                email='staff@example.com',
                password='staff123'
            )
            staff.profile.role = 'STAFF'
            staff.profile.is_role_approved = True
            staff.profile.save(update_fields=['role', 'is_role_approved'])
            self.stdout.write(self.style.SUCCESS('Staff user created (username: staff, password: staff123)'))

        # Create test user
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            self.stdout.write(self.style.SUCCESS('Test user created (username: testuser, password: testpass123)'))

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
        self.stdout.write(f'Created: {Cinema.objects.count()} cinemas')
        self.stdout.write(f'Created: {Screen.objects.count()} screens')
        self.stdout.write(f'Created: {Seat.objects.count()} seats')
        self.stdout.write(f'Created: {Movie.objects.count()} movies')
        self.stdout.write(f'Created: {Show.objects.count()} shows')
