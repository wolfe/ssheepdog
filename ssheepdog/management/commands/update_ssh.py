from django.core.management.base import BaseCommand
from ssheepdog.sync import test_sync


class Command(BaseCommand):
    def handle(self, *args, **options):
        test_sync()
