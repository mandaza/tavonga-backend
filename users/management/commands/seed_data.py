from django.core.management.base import BaseCommand
from users.models import User
from behaviors.models import BehaviorLog
from activities.models import Activity, ActivityLog
from goals.models import Goal
from shifts.models import Shift
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed the database with initial demo data'

    def handle(self, *args, **kwargs):
        # Create admin
        admin, _ = User.objects.get_or_create(
            username='admin', defaults={
                'email': 'admin@example.com',
                'is_admin': True,
                'is_superuser': True,
                'is_staff': True,
                'approved': True
            })
        admin.set_password('admin123')
        admin.save()

        # Create carer
        carer, _ = User.objects.get_or_create(
            username='carer1', defaults={
                'email': 'carer1@example.com',
                'is_admin': False,
                'approved': True
            })
        carer.set_password('carer123')
        carer.save()

        # Create a goal
        goal, _ = Goal.objects.get_or_create(
            name='Improve Communication Skills',
            defaults={
                'description': 'Help client develop better communication skills',
                'category': 'Communication',
                'priority': 'high',
                'created_by': admin,
                'progress_percentage': 20
            })
        goal.assigned_carers.add(carer)

        # Create an activity
        activity, _ = Activity.objects.get_or_create(
            name='Morning Exercise',
            defaults={
                'description': 'Daily morning exercise routine',
                'category': 'therapeutic',
                'difficulty': 'medium',
                'instructions': 'Stretch, jog, cool down',
                'created_by': admin,
                'goal': goal
            })

        # Create an activity log
        activity_log, _ = ActivityLog.objects.get_or_create(
            activity=activity,
            user=carer,
            date=timezone.now().date(),
            defaults={
                'status': 'completed',
                'completed': True,
                'notes': 'Completed successfully.'
            })

        # Create a behavior log
        behavior_log, _ = BehaviorLog.objects.get_or_create(
            user=carer,
            date=timezone.now().date(),
            time=timezone.now().time(),
            defaults={
                'location': 'home',
                'behavior_type': 'aggression',
                'behaviors': ['Shouting'],
                'severity': 'medium',
                'intervention_used': 'Verbal redirection'
            })

        # Create a shift
        shift, _ = Shift.objects.get_or_create(
            carer=carer,
            date=timezone.now().date(),
            defaults={
                'shift_type': 'morning',
                'start_time': timezone.now().replace(hour=8, minute=0, second=0, microsecond=0).time(),
                'end_time': timezone.now().replace(hour=16, minute=0, second=0, microsecond=0).time(),
                'status': 'completed',
                'location': 'Client Home'
            })

        self.stdout.write(self.style.SUCCESS('Seed data created!')) 