from django.core.management.base import BaseCommand
from django.utils import timezone
from chatbot.models import UserSession


class Command(BaseCommand):
    help = 'Clean up expired, inactive, and stale user sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting session cleanup...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No sessions will be deleted'))
        
        # Get counts before cleanup
        total_before = UserSession.objects.count()
        active_before = UserSession.objects.filter(is_active=True).count()
        
        if verbose:
            self.stdout.write(f'Total sessions before cleanup: {total_before}')
            self.stdout.write(f'Active sessions before cleanup: {active_before}')
        
        if not dry_run:
            # Perform cleanup
            cleanup_stats = UserSession.cleanup_all_old_sessions()
            
            # Get counts after cleanup
            total_after = UserSession.objects.count()
            active_after = UserSession.objects.filter(is_active=True).count()
            
            self.stdout.write(self.style.SUCCESS(f'Cleanup completed:'))
            self.stdout.write(f'  - Expired sessions removed: {cleanup_stats["expired"]}')
            self.stdout.write(f'  - Inactive sessions removed: {cleanup_stats["inactive"]}')
            self.stdout.write(f'  - Stale sessions removed: {cleanup_stats["stale"]}')
            self.stdout.write(f'  - Total sessions removed: {cleanup_stats["total"]}')
            self.stdout.write(f'  - Sessions remaining: {total_after}')
            self.stdout.write(f'  - Active sessions remaining: {active_after}')
            
            if verbose:
                remaining_sessions = UserSession.objects.filter(is_active=True).select_related('user')
                self.stdout.write('\nRemaining active sessions:')
                for session in remaining_sessions:
                    last_activity = session.last_activity.strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f'  - {session.user.email} ({session.device_info}) - Last activity: {last_activity}')
        else:
            # Dry run - show what would be deleted
            expired_count = UserSession.objects.filter(expires_at__lt=timezone.now()).count()
            inactive_count = UserSession.objects.filter(is_active=False).count()
            stale_count = UserSession.objects.filter(
                is_active=True,
                last_activity__lt=timezone.now() - timezone.timedelta(minutes=30)
            ).count()
            
            self.stdout.write(self.style.WARNING(f'Would remove:'))
            self.stdout.write(f'  - Expired sessions: {expired_count}')
            self.stdout.write(f'  - Inactive sessions: {inactive_count}')
            self.stdout.write(f'  - Stale sessions: {stale_count}')
            self.stdout.write(f'  - Total that would be removed: {expired_count + inactive_count + stale_count}')
            
            if verbose:
                stale_sessions = UserSession.objects.filter(
                    is_active=True,
                    last_activity__lt=timezone.now() - timezone.timedelta(minutes=30)
                ).select_related('user')
                
                if stale_sessions.exists():
                    self.stdout.write('\nStale sessions that would be removed:')
                    for session in stale_sessions:
                        last_activity = session.last_activity.strftime('%Y-%m-%d %H:%M:%S')
                        self.stdout.write(f'  - {session.user.email} ({session.device_info}) - Last activity: {last_activity}')
        
        self.stdout.write(self.style.SUCCESS('Session cleanup finished.')) 