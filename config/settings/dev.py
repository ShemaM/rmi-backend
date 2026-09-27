from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
    "rest_framework.authentication.BasicAuthentication",  # handy for the browsable API
]
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
