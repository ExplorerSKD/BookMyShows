from django.core.management.base import BaseCommand
from core.models import Movie
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test movie detail page improvements'

    def add_arguments(self, parser):
        parser.add_argument('movie_id', type=int, nargs='?', default=None, 
                           help='ID of the movie to test (optional)')

    def handle(self, *args, **options):
        movie_id = options['movie_id']
        
        if movie_id:
            try:
                movie = Movie.objects.get(id=movie_id)
                self.stdout.write(f'Testing movie detail page for: {movie.title}')
                self.stdout.write(f'Organizer: {movie.organizer.username if movie.organizer else "None"}')
                self.stdout.write(f'Promoted: {movie.is_promoted}')
                self.stdout.write(f'Has trailer: {bool(movie.trailer_url)}')
                self.stdout.write(f'Description length: {len(movie.description)} characters')
                self.stdout.write(self.style.SUCCESS('Movie detail page ready for testing!'))
            except Movie.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Movie with ID {movie_id} does not exist.'))
        else:
            # Show all movies with their details
            movies = Movie.objects.all()
            self.stdout.write('Available movies for testing:')
            self.stdout.write('=' * 50)
            
            for movie in movies:
                self.stdout.write(f'ID: {movie.id} | Title: {movie.title}')
                self.stdout.write(f'  - Organizer: {movie.organizer.username if movie.organizer else "None"}')
                self.stdout.write(f'  - Promoted: {movie.is_promoted}')
                self.stdout.write(f'  - Has trailer: {bool(movie.trailer_url)}')
                self.stdout.write(f'  - Genre: {movie.genre}')
                self.stdout.write(f'  - Language: {movie.language}')
                self.stdout.write('-' * 30)
            
            self.stdout.write(self.style.SUCCESS('Use "python manage.py test_movie_detail <movie_id>" to test a specific movie.'))