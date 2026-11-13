"""
Demo data for presentations.

    python manage.py seed_demo --reset    # wipe ALL data, then seed (the one command)
    python manage.py seed_demo            # seed into an empty database

Everything is created through the real services, so if this command fails,
the traceback points at a broken service or a missing PERMISSIONS entry.
That makes it a quick smoke test before a demo, too.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from finance.models import LedgerEntry, SpendingReq  # noqa: F401  (used through backdate)
from finance.services import (
    bal_adjustment,
    request_approve,
    request_complete,
    request_deny,
    request_reim,
    request_spending,
)
from organizations.models import Membership
# If an import below fails, that function lives in the other app's services.py; move it to that import line.
from organizations.services import change_role, create_org, join_org, overspend_adjustment

PASSWORD = "demo-pass-123"  # demo accounts only, never on a deployed site


def month_ago(n, day=15):
    """Noon local time on `day` of the month that is n months before the current one."""
    now = timezone.localtime()
    year, month = now.year, now.month - n
    while month <= 0:
        month += 12
        year -= 1
    return timezone.make_aware(datetime(year, month, day, 12, 0))


def backdate(obj, when):
    """auto_now_add ignores any date passed on create, so overwrite created_at afterwards.
    .update() writes straight to the database and skips the automatic timestamp."""
    type(obj).objects.filter(pk=obj.pk).update(created_at=when)


class Command(BaseCommand):
    help = "Create demo users, two orgs, and five months of spending history."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Delete ALL data first (flush), then seed.")

    def handle(self, *args, **options):
        User = get_user_model()
        if options["reset"]:
            call_command("flush", interactive=False, verbosity=0)
        elif User.objects.exists():
            raise CommandError("The database isn't empty. Run `python manage.py seed_demo --reset` to wipe it first.")

        # All or nothing: if any step fails, no half-built demo data is left behind.
        with transaction.atomic():
            self.seed(User)

        self.stdout.write(self.style.SUCCESS("Demo data created. Every account's password is: " + PASSWORD))
        for line in [
            "admin@demo.com   superuser (Django admin)",
            "alice@demo.com   Chess Club president",
            "ben@demo.com     Chess Club treasurer",
            "cara@demo.com    Chess Club member",
            "dev@demo.com     Chess Club member",
            "erin@demo.com    Robotics Club president (not in Chess Club)",
            "felix@demo.com   Robotics Club member",
        ]:
            self.stdout.write("  " + line)

    def make_user(self, User, first, last):
        email = f"{first.lower()}@demo.com"
        return User.objects.create_user(username=email, email=email, password=PASSWORD,
                                        first_name=first, last_name=last)

    def seed(self, User):
        User.objects.create_superuser(username="admin@demo.com", email="admin@demo.com", password=PASSWORD)

        alice = self.make_user(User, "Alice", "Ng")
        ben = self.make_user(User, "Ben", "Okafor")
        cara = self.make_user(User, "Cara", "Diaz")
        dev = self.make_user(User, "Dev", "Patel")
        erin = self.make_user(User, "Erin", "Walsh")
        felix = self.make_user(User, "Felix", "Moreau")

        # ---- Chess Club: the org you demo ----
        chess = create_org(actor=alice, name="Chess Club")
        for person in (ben, cara, dev):
            join_org(actor=person, code=chess.join_code)
        ben_membership = Membership.objects.get(user=ben, organization=chess)
        change_role(actor=alice, membership_id=ben_membership.id, org=chess,
                    new_role=Membership.Role.TREASURER)
        overspend_adjustment(actor=alice, org=chess, new_limit=Decimal("10"))

        def ledger_adjustment(amount, title, months):
            entry = bal_adjustment(actor=alice, org=chess, adjustment=Decimal(amount), title=title)
            backdate(entry, month_ago(months))

        def paid_request(person, title, spend, reim, months):
            req = request_spending(actor=person, org=chess, title=title, spend=Decimal(spend))
            request_approve(actor=ben, request_id=req.id, org=chess)
            request_reim(actor=person, request_id=req.id, org=chess, reimamount=Decimal(reim))
            entry = request_complete(actor=ben, request_id=req.id, org=chess)
            backdate(req, month_ago(months, day=5))
            backdate(entry, month_ago(months, day=20))

        # Five months of history, one closing balance per month for the graph.
        ledger_adjustment("800", "Semester dues", 5)                      # 800
        paid_request(cara, "Tournament entry fees", "120", "120", 4)      # 680
        ledger_adjustment("300", "Bake sale fundraiser", 3)
        paid_request(dev, "New chess sets", "200", "215", 3)              # 765  ($15 over spend, limit $10: flagged)
        paid_request(cara, "Pizza for club night", "60", "58", 2)         # 707
        ledger_adjustment("-25", "Bank fee correction", 1)                # 682

        # This month: one request in each open state, ready for the live demo.
        request_spending(actor=cara, org=chess, title="Replacement boards", spend=Decimal("90"))      # pending
        flyers = request_spending(actor=dev, org=chess, title="Flyer printing", spend=Decimal("40"))
        request_approve(actor=ben, request_id=flyers.id, org=chess)                                    # approved
        snacks = request_spending(actor=cara, org=chess, title="Snacks for open house", spend=Decimal("50"))
        request_approve(actor=ben, request_id=snacks.id, org=chess)
        request_reim(actor=cara, request_id=snacks.id, org=chess, reimamount=Decimal("55"))           # submitted, within limit
        party = request_spending(actor=dev, org=chess, title="End-of-year party", spend=Decimal("400"))
        request_deny(actor=ben, request_id=party.id, org=chess)                                        # denied

        # ---- Robotics Club: a second org, to show Chess Club can't see it ----
        robotics = create_org(actor=erin, name="Robotics Club")
        join_org(actor=felix, code=robotics.join_code)
        grant = bal_adjustment(actor=erin, org=robotics, adjustment=Decimal("1500"), title="Department grant")
        backdate(grant, month_ago(2))
        request_spending(actor=felix, org=robotics, title="Servo motors", spend=Decimal("230"))
