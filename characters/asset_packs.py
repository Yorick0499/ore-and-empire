"""Offline image validation and pre-request redirect checks."""
import hashlib
import io
import warnings
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler
from PIL import Image

MAX_BYTES=5*1024*1024
MAX_PIXELS=16_000_000
MIME={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}


def trusted(url):
    parsed=urlsplit(url)
    return parsed.scheme=='https' and parsed.hostname in {'gothic.fandom.com','static.wikia.nocookie.net'} and parsed.username is None and parsed.password is None and parsed.port in (None,443)


class TrustedRedirect(HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        if not trusted(newurl): raise ValueError('Unexpected redirect host before request')
        return super().redirect_request(request,fp,code,msg,headers,newurl)


def validate_image(body,mime=None):
    if not body or len(body)>MAX_BYTES: raise ValueError('Image exceeds byte limit')
    with warnings.catch_warnings():
        warnings.simplefilter('error',Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(body),formats=['PNG','JPEG','WEBP']) as image:
            width,height=image.size
            detected=MIME.get(image.format)
            if not 0<width<=8192 or not 0<height<=8192 or width*height>MAX_PIXELS or (mime and mime!=detected): raise ValueError('Invalid image dimensions/type')
            if getattr(image,'n_frames',1)!=1: raise ValueError('Animated images not supported in content packs')
            image.verify()
        with Image.open(io.BytesIO(body)) as image: image.load()
    return {'sha256':hashlib.sha256(body).hexdigest(),'width':width,'height':height,'mime':detected}
