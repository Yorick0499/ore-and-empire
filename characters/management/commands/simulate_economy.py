import json
from pathlib import Path
from django.core.management.base import BaseCommand
from characters.economy_simulation import simulation_report


class Command(BaseCommand):
    help='Offline 10/30/90-day budget stress matrix; does not modify player saves.'
    def add_arguments(self,parser):parser.add_argument('--output',type=Path)
    def handle(self,*args,**options):
        raw=json.dumps(simulation_report(),ensure_ascii=False,indent=2)+'\n'
        if options['output']:
            options['output'].parent.mkdir(parents=True,exist_ok=True);options['output'].write_text(raw)
            self.stdout.write('Wrote deterministic model report; live world unchanged.')
        else:self.stdout.write(raw)
