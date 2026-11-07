"""Django fixtures with full microsecond precision, for lossless save migration."""
from datetime import datetime
from django.core.serializers.json import Serializer as JSONSerializer,Deserializer,DjangoJSONEncoder

class PreciseEncoder(DjangoJSONEncoder):
    def default(self,value):
        if isinstance(value,datetime):
            result=value.isoformat(timespec='microseconds')
            return result[:-6]+'Z' if result.endswith('+00:00') else result
        return super().default(value)

class Serializer(JSONSerializer):
    def _init_options(self):
        super()._init_options()
        self.json_kwargs['cls']=PreciseEncoder
