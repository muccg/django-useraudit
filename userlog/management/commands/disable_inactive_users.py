from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.sites.shortcuts import get_current_site
from ...password_expiry import ExpirySettings, logger


class Command(BaseCommand):
    help = """
       Finds all users who haven't logged in recently enough and
       deactivates them.
    """

    def add_arguments(self, parser):
        parser.add_argument("--no-email", "-e", help="Don't notify users by e-mail",
                            dest="email", action="store_false", default=True)

    def handle(self, email=True, verbosity=1, **kwargs):
        self.verbosity = verbosity

        UserModel = get_user_model()
        exp = ExpirySettings.get()
        oldest = exp.earliest_possible_login

        if oldest is None:
            self._info("Account expiry not configured; nothing to do.")
            return

        self._info("Checking for users who haven't logged in since %s" % oldest)

        gone = UserModel.objects.filter(is_active=True, last_login__lt=oldest)

        for username in gone.values_list(UserModel.USERNAME_FIELD, flat=True):
            self._info("Deactiviting user: %s" % username)

        messages = list(filter(None, (self._make_email(exp, user) for user in gone)))

        count = gone.update(is_active=False)
        if count:
            self._info("%d account(s) expired" % count)

        if email and messages:
            self._info("Sending e-mails")
            connection = mail.get_connection()
            connection.send_messages(messages)

        self._info("Done")

    def _info(self, msg):
        if self.verbosity:
            self.stdout.write(msg + "\n")

    def _make_email(self, exp, user):
        site = get_current_site(None)
        subject = "[%s] Your account has expired" % site.name
        to_email = getattr(user, "email", None)
        msg = """Dear {full_name},

This is an automatic message from the {name} system.

If accounts are not used for a period of {expiry_days} days, they will
be deactivated. The last time your user logged in was {last_login}.

If you do not need your account any more, you can disregard this
message. We wish you well for all your future endeavours.

Otherwise, please get in contact with the site administrators to have
your account reset.

{name} System
        """.format(name=site.name, expiry_days=exp.account_expiry,
                   last_login=user.last_login.strftime("%x"),
                   full_name=user.get_full_name())

        if to_email:
            return mail.EmailMessage(subject, msg, None, [to_email])
        else:
            self._info("Could not determine an e-mail address for %s" % user)
            return None
