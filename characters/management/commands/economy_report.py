import json
from django.core.management.base import BaseCommand
from characters.economic_ledger import summary


class Command(BaseCommand):
    help='Read-only aggregate currency reconciliation; transfer turnover is separate.'
    def handle(self,*args,**options):self.stdout.write(json.dumps(summary(),ensure_ascii=False,indent=2))
