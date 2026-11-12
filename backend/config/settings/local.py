from .base import *

from corsheaders.defaults import default_headers

DEBUG = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CORS_ALLOW_HEADERS = [
    *default_headers,
    "x-upload-token",
]