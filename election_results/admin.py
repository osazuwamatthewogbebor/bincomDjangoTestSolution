from django.contrib import admin
from .models import *

from django.apps import apps

app = apps.get_app_config('election_results')

for model in app.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass

