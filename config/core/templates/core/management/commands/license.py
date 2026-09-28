from django.core.management.base import BaseCommand
from core.models import BankLicense
from datetime import date, timedelta

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('bank', type=str)
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **options):
        bank = options['bank']
        days = options['days']
        lic = BankLicense.objects.create(
            bank_name=bank,
            license_key=BankLicense.generate_key(),
            valid_until=date.today() + timedelta(days=days)
        )
        self.stdout.write(self.style.SUCCESS(f"LICENSE CREATED FOR {bank}"))
        self.stdout.write(f"KEY: {lic.license_key}")
        self.stdout.write(f"VALID TILL: {lic.valid_until}")