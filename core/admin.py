"""
Admin configuration for core app
"""
from django.contrib import admin
from .models import Cinema, Screen, Seat, Movie, Show, Booking, SeatLock, UserProfile


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'address', 'created_at']
    list_filter = ['city']
    search_fields = ['name', 'city']


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'cinema', 'total_seats', 'created_at']
    list_filter = ['cinema']
    search_fields = ['name', 'cinema__name']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'screen', 'seat_type', 'created_at']
    list_filter = ['seat_type', 'screen']
    search_fields = ['number', 'screen__name']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'genre', 'duration_mins', 'created_at']
    list_filter = ['language', 'genre']
    search_fields = ['title']


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['movie', 'screen', 'date', 'start_time', 'price']
    list_filter = ['date', 'screen__cinema']
    search_fields = ['movie__title', 'screen__name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'show', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['booking_id', 'user__username']
    readonly_fields = ['booking_id']


@admin.register(SeatLock)
class SeatLockAdmin(admin.ModelAdmin):
    list_display = ['show', 'seat_number', 'user', 'locked_at', 'expires_at', 'is_expired_status']
    list_filter = ['locked_at', 'expires_at']
    search_fields = ['seat_number', 'user__username', 'show__movie__title']
    readonly_fields = ['locked_at', 'is_expired_status']
    actions = ['release_expired_locks_action']
    
    @admin.display(description='Expired?', boolean=True)
    def is_expired_status(self, obj):
        return obj.is_expired()
        
    @admin.action(description='Release selected expired locks')
    def release_expired_locks_action(self, request, queryset):
        from django.utils import timezone
        now = timezone.now()
        expired_locks = queryset.filter(expires_at__lte=now)
        count = expired_locks.count()
        expired_locks.delete()
        self.message_user(request, f'Released {count} expired seat locks.')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'role_status', 'is_role_approved']
    list_filter = ['role', 'is_role_approved']
    search_fields = ['user__username', 'user__email']
    actions = ['approve_selected_roles', 'mark_selected_pending']

    @admin.display(description='Status', ordering='is_role_approved')
    def role_status(self, obj):
        return 'Approved' if obj.is_role_approved else 'Pending approval'

    def approve_selected_roles(self, request, queryset):
        updated = queryset.update(is_role_approved=True)
        self.message_user(request, f'Approved {updated} profile(s).')
    approve_selected_roles.short_description = 'Approve selected roles'

    def mark_selected_pending(self, request, queryset):
        updated = queryset.update(is_role_approved=False)
        self.message_user(request, f'Marked {updated} profile(s) as pending.')
    mark_selected_pending.short_description = 'Mark selected roles as pending'
