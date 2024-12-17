from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Assign custom permissions to the developer user'

    def handle(self, *args, **kwargs):
        developer_username = 'developer_username'  # Replace with the actual developer username
        try:
            developer = User.objects.get(username=developer_username)
            content_type = ContentType.objects.get(app_label='your_app', model='activitylog')
            permission = Permission.objects.get(codename='view_activity_log', content_type=content_type)
            developer.user_permissions.add(permission)
            self.stdout.write(self.style.SUCCESS(f'Successfully assigned permission to {developer_username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {developer_username} does not exist'))
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR('Permission view_activity_log does not exist'))
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR('Content type for ActivityLog does not exist'))
