# Generated migration for adding activity relationships to BehaviorLog

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0001_initial'),  # Adjust based on your actual migration
        ('behaviors', '0001_initial'),   # Adjust based on your actual migration
    ]

    operations = [
        migrations.AddField(
            model_name='behaviorlog',
            name='related_activity',
            field=models.ForeignKey(
                blank=True,
                help_text='Activity associated with this behavior',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='behavior_logs',
                to='activities.activity'
            ),
        ),
        migrations.AddField(
            model_name='behaviorlog',
            name='related_activity_log',
            field=models.ForeignKey(
                blank=True,
                help_text='Specific activity log instance associated with this behavior',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='behavior_logs',
                to='activities.activitylog'
            ),
        ),
        migrations.AddField(
            model_name='behaviorlog',
            name='behavior_occurrence',
            field=models.CharField(
                choices=[
                    ('before_activity', 'Before Activity'),
                    ('during_activity', 'During Activity'),
                    ('after_activity', 'After Activity'),
                    ('unrelated', 'Unrelated to Activity')
                ],
                default='unrelated',
                help_text='When the behavior occurred relative to the activity',
                max_length=20
            ),
        ),
    ] 