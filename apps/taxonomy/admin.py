from django.contrib import admin

from .models import Country, Region, Theme

admin.site.register((Region, Country, Theme))
