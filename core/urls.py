"""
URL configuration for core app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Home and movies
    path('', views.welcome_page, name='home'),
    path('movies/', views.home, name='movies'),
    path('movies/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    
    # Shows and booking
    path('shows/<int:show_id>/', views.show_page, name='show_page'),
    
    # API endpoints
    path('api/lock_seats/', views.lock_seats, name='lock_seats'),
    path('api/confirm_booking/', views.confirm_booking, name='confirm_booking'),
    path('api/create_order/', views.create_order, name='create_order'),
    path('api/movies/', views.movies_list_api, name='movies_list_api'),
    path('api/meta/', views.movies_meta_api, name='movies_meta_api'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('organizer/login/', views.organizer_login_view, name='organizer_login'),
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    
    # Admin dashboard (also exposed at project level /admin/dashboard/)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Organizer and staff routes
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('organizer/movies/add/', views.organizer_movie_create, name='organizer_movie_create'),
    path('organizer/movies/<int:movie_id>/edit/', views.organizer_movie_edit, name='organizer_movie_edit'),
    path('organizer/movies/<int:movie_id>/delete/', views.organizer_movie_delete, name='organizer_movie_delete'),
    path('organizer/wallet/', views.wallet_view, name='wallet_view'),
    path('organizer/movies/<int:movie_id>/promote/', views.promote_movie, name='promote_movie'),
    
    path('admin/gift-funds/', views.admin_gift_funds, name='admin_gift_funds'),
    
    path('staff/scan/', views.staff_scan_ticket, name='staff_scan_ticket'),
]
