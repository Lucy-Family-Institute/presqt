from django.core.management import BaseCommand
from django.utils import timezone

from authentication.models import UserAuthentication


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Delete all user_authentication from the DB.
        """
        today = timezone.now().strftime("%m/%d/%Y")
        print(f'Deleting all users from {today}.')
        print('...........')
        UserAuthentication.objects.all().delete()
        print(f'All users from {today} have been deleted.')
