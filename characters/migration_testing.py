"""Serialize a historical test fixture without adding fake columns to its database."""
import json
from django.apps import apps as current_apps
from django.core import serializers


def historical_fixture(state_apps, excludes):
    rows=[]
    for model in current_apps.get_models():
        if model._meta.label_lower in excludes or model._meta.app_label in excludes:continue
        try:old=state_apps.get_model(model._meta.app_label,model._meta.model_name)
        except LookupError:continue
        # Current natural-key methods remain available, but SQL and field access
        # are restricted to columns that genuinely existed in the old snapshot.
        fields=[f.name for f in (*old._meta.local_fields,*old._meta.local_many_to_many)]
        query=model._base_manager.only(*(f.attname for f in old._meta.concrete_fields)).order_by('pk')
        rows.extend(json.loads(serializers.serialize('precise_json',query,fields=fields,use_natural_foreign_keys=True)))
    return json.dumps(rows,ensure_ascii=False)
