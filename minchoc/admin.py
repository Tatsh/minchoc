from django.contrib import admin

from .models import Company, NugetUser, Package

admin.site.register(Company)
admin.site.register(NugetUser)
admin.site.register(Package)
