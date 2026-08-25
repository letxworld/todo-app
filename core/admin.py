from django.contrib import admin
from django.apps import apps

# Get the configuration object for your specific app
app_models = apps.get_app_config('core').get_models()

# Dynamically register every model found in this app
for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
