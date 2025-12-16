from django.core.management.base import BaseCommand
from core.models import Movie, Wallet
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test movie promotion functionality'

    def add_arguments(self, parser):
        parser.add_argument('movie_id', type=int, help='ID of the movie to promote')
        parser.add_argument('organizer_username', type=str, help='Username of the organizer')

    def handle(self, *args, **options):
        movie_id = options['movie_id']
        organizer_username = options['organizer_username']
        
        try:
            # Get the movie and organizer
            movie = Movie.objects.get(id=movie_id)
            organizer = User.objects.get(username=organizer_username)
            
            self.stdout.write(f'Testing promotion for movie: {movie.title}')
            self.stdout.write(f'Organizer: {organizer.username}')
            self.stdout.write(f'Movie currently promoted: {movie.is_promoted}')
            
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=organizer)
            initial_balance = wallet.balance
            
            self.stdout.write(f'Initial wallet balance: ₹{initial_balance}')
            
            # Test promotion
            if movie.is_promoted:
                self.stdout.write('Movie is already promoted.')
            else:
                # Add funds if needed
                if wallet.balance < 500:
                    wallet.add_funds(1000)
                    self.stdout.write('Added ₹1000 to wallet for testing.')
                
                # Promote the movie
                if wallet.deduct_funds(500):
                    movie.is_promoted = True
                    movie.save()
                    self.stdout.write(
                        self.style.SUCCESS('Movie promoted successfully!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to promote movie - insufficient funds.')
                    )
            
            # Show final status
            movie.refresh_from_db()
            wallet.refresh_from_db()
            self.stdout.write(f'Movie promoted status: {movie.is_promoted}')
            self.stdout.write(f'Final wallet balance: ₹{wallet.balance}')
            
        except Movie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Movie with ID {movie_id} does not exist.')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {organizer_username} does not exist.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )