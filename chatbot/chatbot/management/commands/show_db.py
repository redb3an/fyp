from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.models import UserProfile, ChatHistory
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count

class Command(BaseCommand):
    help = 'Display database contents based on user role'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to view data as')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))
            return

        if user.is_superuser:
            self._show_admin_view()
        else:
            self._show_user_view(user)

    def _show_user_view(self, user):
        self.stdout.write(self.style.SUCCESS(f'\n=== Your Chat History ({user.username}) ==='))
        
        # Show user's profile
        try:
            profile = user.profile
            self.stdout.write(f'\nYour Profile:')
            self.stdout.write(f'Full name: {profile.full_name}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Joined: {user.date_joined}')
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.WARNING('No profile found'))

        # Show user's chat history
        chats = ChatHistory.objects.filter(user=user).order_by('-timestamp')
        if not chats:
            self.stdout.write('\nNo chat history found')
        else:
            self.stdout.write('\nYour Recent Conversations:')
            for chat in chats:
                self.stdout.write(self.style.SUCCESS(f'\nTime: {chat.timestamp}'))
                self.stdout.write(f'You: {chat.message}')
                self.stdout.write(f'Bot: {chat.response}')

    def _show_admin_view(self):
        self.stdout.write(self.style.SUCCESS('\n=== Admin Analytics Dashboard ==='))

        # User Statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        superusers = User.objects.filter(is_superuser=True).count()

        self.stdout.write('\nUser Statistics:')
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'Active Users: {active_users}')
        self.stdout.write(f'Superusers: {superusers}')

        # Chat Statistics
        total_chats = ChatHistory.objects.count()
        today = timezone.now()
        chats_today = ChatHistory.objects.filter(
            timestamp__date=today.date()
        ).count()
        chats_this_week = ChatHistory.objects.filter(
            timestamp__gte=today - timedelta(days=7)
        ).count()

        self.stdout.write('\nChat Statistics:')
        self.stdout.write(f'Total Conversations: {total_chats}')
        self.stdout.write(f'Conversations Today: {chats_today}')
        self.stdout.write(f'Conversations This Week: {chats_this_week}')

        # Most Active Users
        most_active_users = ChatHistory.objects.values(
            'user__username', 'user__email'
        ).annotate(
            chat_count=Count('id')
        ).order_by('-chat_count')[:5]

        self.stdout.write('\nMost Active Users:')
        for user in most_active_users:
            self.stdout.write(f"{user['user__username']} ({user['user__email']}): {user['chat_count']} chats")

        # All Users and Their Chats
        self.stdout.write(self.style.SUCCESS('\n=== All Users and Their Conversations ==='))
        users = User.objects.all().order_by('date_joined')
        
        for user in users:
            self.stdout.write(self.style.SUCCESS(f'\nUser: {user.username}'))
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Joined: {user.date_joined}')
            self.stdout.write(f'Status: {"Superuser" if user.is_superuser else "Regular User"}')
            
            try:
                profile = user.profile
                self.stdout.write(f'Full name: {profile.full_name}')
            except UserProfile.DoesNotExist:
                self.stdout.write('No profile found')

            # Show user's recent chats
            chats = ChatHistory.objects.filter(user=user).order_by('-timestamp')[:5]
            if chats:
                self.stdout.write('\nRecent Conversations:')
                for chat in chats:
                    self.stdout.write(f'\nTime: {chat.timestamp}')
                    self.stdout.write(f'Message: {chat.message[:100]}...' if len(chat.message) > 100 else f'Message: {chat.message}')
                    self.stdout.write(f'Response: {chat.response[:100]}...' if len(chat.response) > 100 else f'Response: {chat.response}') 