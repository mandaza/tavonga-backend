from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count
from collections import defaultdict

User = get_user_model()

class Command(BaseCommand):
    help = 'Check for and optionally clean up duplicate users by email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix duplicates (keep most recent active admin, or most recent active user, or most recent user)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it (default behavior)',
        )

    def handle(self, *args, **options):
        # Find emails with multiple users
        duplicate_emails = User.objects.values('email')\
            .annotate(count=Count('id'))\
            .filter(count__gt=1)\
            .values_list('email', flat=True)

        if not duplicate_emails:
            self.stdout.write('✓ No duplicate emails found!')
            return

        self.stdout.write(f'Found {len(duplicate_emails)} email(s) with duplicates:')
        
        total_duplicates_removed = 0
        
        for email in duplicate_emails:
            users = User.objects.filter(email=email).order_by('-created_at')
            self.stdout.write(f'\nEmail: {email} ({users.count()} users)')
            
            # Show all users with this email
            for i, user in enumerate(users):
                status_info = []
                if user.is_active:
                    status_info.append('active')
                else:
                    status_info.append('inactive')
                    
                if user.is_admin:
                    status_info.append('admin')
                    
                if user.approved:
                    status_info.append('approved')
                else:
                    status_info.append('not approved')
                    
                status_str = ', '.join(status_info)
                marker = '[KEEP]' if i == 0 else '[REMOVE]'
                
                self.stdout.write(f'  {marker} ID: {user.id}, Username: {user.username}, '
                                f'Created: {user.created_at}, Status: {status_str}')
            
            if options['fix']:
                # Keep the first user (most recent) and delete the rest
                users_to_keep = users.first()
                users_to_delete = users[1:]
                
                for user_to_delete in users_to_delete:
                    self.stdout.write(f'    Deleting user ID {user_to_delete.id} ({user_to_delete.username})')
                    user_to_delete.delete()
                    total_duplicates_removed += 1
                    
                self.stdout.write(f'    Kept user ID {users_to_keep.id} ({users_to_keep.username})')
            
        if options['fix']:
            self.stdout.write(f'\n✓ Removed {total_duplicates_removed} duplicate users.')
        else:
            self.stdout.write(f'\n⚠️  Found {sum(User.objects.filter(email=email).count() - 1 for email in duplicate_emails)} duplicate users.')
            self.stdout.write('Run with --fix to actually remove duplicates, keeping the most recently created user for each email.')
            self.stdout.write('Priority order: Most recent creation date (regardless of other attributes)') 