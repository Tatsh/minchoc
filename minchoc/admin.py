from django.contrib import admin

from .models import Author, Company, NugetUser, Package

admin.site.register(Author)
admin.site.register(Company)
admin.site.register(NugetUser)
admin.site.register(Package)
