"""Optional metrics from isolated integration scenarios; never invoked by gameplay."""
import json
import os
from pathlib import Path


def record_scenario(name, facts):
    target = os.environ.get('ORE_PROBE_REPORT')
    if not target:return
    path = Path(target)
    records = json.loads(path.read_text())
    records.append({'scenario':name,**facts})
    path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
