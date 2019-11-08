from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from useraudit.models import UserDeactivation

class Command(BaseCommand):
    help = """
       Activates an inactive user.
    """

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='+', help='The user(s) to activate')

    def handle(self, **options):
        users = map(self._load_user, options['username'])
        with transaction.atomic():
            for user in users:
                self._activate_user(user)

    def _load_user(self, username):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            raise CommandError('User "%s" does NOT exist' % username)

    def _activate_user(self, user):
        if user.is_active:
            self.stdout.write('Ignoring already active user "%s"\n' % user.username)
            return
        user.is_active = True
        user.save()
        UserDeactivation.objects.filter(username=user.username).delete()
