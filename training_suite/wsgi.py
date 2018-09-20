"""
WSGI config for training_suite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise
import newrelic.agent

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "training_suite.settings")

newrelic.agent.initialize()

application = get_wsgi_application()
# https://devcenter.heroku.com/articles/django-assets#collectstatic-during-builds
application = newrelic.agent.WSGIApplicationWrapper(DjangoWhiteNoise(application))
